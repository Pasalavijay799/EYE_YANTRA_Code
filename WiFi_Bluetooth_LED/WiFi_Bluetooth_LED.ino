/*
  AMB82 Mini: Dynamic WiFi Configuration via Flask and MJPEG Stream
  - BLE for WiFi credentials & LED control
  - HTTP stream for MJPEG video
  - Built-in LED control via Flask commands ("LightOn", "LightOff")
*/

#include <WiFi.h>
#include "VideoStream.h"
#include "BLEDevice.h"

#define CHANNEL 0
//#define LED_BUILTIN 13  // Adjust based on your board

// Video Configuration
VideoSetting config(640, 480, 15, VIDEO_JPEG, 1);

// WiFi Credentials
char ssid[32] = "";
char pass[64] = "";
int status = WL_IDLE_STATUS;
WiFiServer server(80);

// BLE UUIDs
#define UART_SERVICE_UUID      "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  // Write
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  // Notify

BLEService UartService(UART_SERVICE_UUID);
BLECharacteristic Rx(CHARACTERISTIC_UUID_RX);
BLECharacteristic Tx(CHARACTERISTIC_UUID_TX);
BLEAdvertData advdata;
BLEAdvertData scndata;

bool notify = false;
uint8_t activeConnID = 0;

// WiFi Connection State
bool wifiConnectRequested = false;
unsigned long lastConnectAttempt = 0;
int wifiRetryCount = 0;
bool cameraStarted = false;

// Stream Parameters
uint32_t img_addr = 0;
uint32_t img_len = 0;
#define PART_BOUNDARY "123456789000000000000987654321"
char* STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
char* IMG_HEADER = "Content-Type: image/jpeg\r\nContent-Length: %lu\r\n\r\n";

// Send HTTP Header for MJPEG Stream
void sendHeader(WiFiClient& client) {
    client.print("HTTP/1.1 200 OK\r\nContent-type: multipart/x-mixed-replace; boundary=");
    client.println(PART_BOUNDARY);
    client.print("Transfer-Encoding: chunked\r\n\r\n");
}

// Send Chunked Data
void sendChunk(WiFiClient& client, uint8_t* buf, uint32_t len) {
    char chunk_buf[64];
    uint8_t chunk_len = snprintf(chunk_buf, 64, "%lX\r\n", len);
    client.write((uint8_t*)chunk_buf, chunk_len);
    client.write(buf, len);
    client.print("\r\n");
}

// BLE Callback: Handle Data from Flask (WiFi Credentials & LED Control)
String bleBuffer = "";
void writeCB(BLECharacteristic* chr, uint8_t connID) {
    activeConnID = connID;
    if (chr->getDataLen() > 0) {
        String receivedData = chr->readString();
        bleBuffer += receivedData;

        int newlineIdx = bleBuffer.indexOf('\n');
        if (newlineIdx >= 0) {
            String fullMessage = bleBuffer.substring(0, newlineIdx);
            bleBuffer = bleBuffer.substring(newlineIdx + 1); // Keep remainder for future packets

            Serial.print("📥 Received from Flask (Full): ");
            Serial.println(fullMessage);

            // Handle LED Commands
            if (fullMessage == "LightOn") {
                digitalWrite(LED_BUILTIN, HIGH);  // Turn on LED
                sendDataToFlask("LightOn");      // Confirm LightOn
                Serial.println("💡 LED ON");

            } else if (fullMessage == "LightOff") {
                digitalWrite(LED_BUILTIN, LOW);   // Turn off LED
                sendDataToFlask("LightOff");      // Confirm LightOff
                Serial.println("💡 LED OFF");

            } else {  
                // Handle WiFi Credentials
                int delimiter = fullMessage.indexOf(',');
                if (delimiter > 0) {
                    fullMessage.substring(0, delimiter).toCharArray(ssid, sizeof(ssid));
                    fullMessage.substring(delimiter + 1).toCharArray(pass, sizeof(pass));

                    Serial.print("📶 Parsed SSID: ");
                    Serial.println(ssid);
                    Serial.print("🔑 Parsed Password: ");
                    Serial.println(pass);
                    
                    status = WL_IDLE_STATUS; // Force reconnection with new credentials
                    wifiConnectRequested = true;
                    wifiRetryCount = 0;
                    lastConnectAttempt = 0; // Trigger immediate connection attempt
                }
            }
        }
    }
}

void notifCB(BLECharacteristic* chr, uint8_t connID, uint16_t cccd) {
    notify = (cccd & GATT_CLIENT_CHAR_CONFIG_NOTIFY) != 0;
    activeConnID = connID;
    if (notify && status == WL_CONNECTED) {
        sendDataToFlask("IP:" + ipToString(WiFi.localIP()));
    }
}

// Helper: Convert IP Address to String
String ipToString(IPAddress ip) {
    char buf[16];
    snprintf(buf, sizeof(buf), "%d.%d.%d.%d", ip[0], ip[1], ip[2], ip[3]);
    return String(buf);
}

// Send Data to Flask via BLE
// Notifications are capped at 20 bytes (default ATT MTU), so messages longer
// than that must be split into chunks; a trailing '\n' lets Flask know where
// one logical message ends, mirroring how writeCB() reassembles incoming data.
void sendDataToFlask(String message) {
    if (BLE.connected(0) && notify) {
        String framed = message + "\n";
        const int chunkSize = 20;
        for (int i = 0; i < (int)framed.length(); i += chunkSize) {
            int end = i + chunkSize;
            if (end > (int)framed.length()) end = framed.length();
            Tx.writeString(framed.substring(i, end));
            Tx.notify(0);
            delay(20); // give the BLE stack time to send before queuing the next packet
        }
        Serial.print("📤 Sent to Flask: ");
        Serial.println(message);
    }
}

// connectToWiFi is replaced by non-blocking logic in loop()

void setup() {
    Serial.begin(115200);

    pinMode(LED_BUILTIN, OUTPUT);  // Initialize LED pin
    digitalWrite(LED_BUILTIN, LOW); // Ensure LED is off at startup

    // BLE Advertising Data
    advdata.addFlags(GAP_ADTYPE_FLAGS_LIMITED | GAP_ADTYPE_FLAGS_BREDR_NOT_SUPPORTED);
    advdata.addCompleteName("AMEBA_BLE_DEV");
    scndata.addCompleteServices(BLEUUID(UART_SERVICE_UUID));

    // Set Up BLE Service
    Rx.setWriteProperty(true);
    Rx.setWritePermissions(GATT_PERM_WRITE);
    Rx.setWriteCallback(writeCB);

    Tx.setReadProperty(true);
    Tx.setNotifyProperty(true);
    Tx.setCCCDCallback(notifCB);

    UartService.addCharacteristic(Rx);
    UartService.addCharacteristic(Tx);
    delay(2000);
    BLE.init();
    BLE.configAdvert()->setAdvData(advdata);
    BLE.configAdvert()->setScanRspData(scndata);
    BLE.configServer(1);
    BLE.addService(UartService);
    BLE.beginPeripheral();
    delay(2000);
    
    Serial.println("🔄 BLE UART Service Started...");
    // Camera is started after WiFi connects (see loop()), matching Realtek's
    // reference order - starting it here while WiFi/BLE pairing is still
    // pending left the encoder idle too long and it came up as "VOE not init".
}

void loop() {
    // Attempt to connect to WiFi non-blockingly if requested and not already connected
    if (wifiConnectRequested && status != WL_CONNECTED) {
        unsigned long currentMillis = millis();
        // Wait 6 seconds between retries to keep BLE alive and responsive
        if (currentMillis - lastConnectAttempt >= 6000) {
            lastConnectAttempt = currentMillis;
            wifiRetryCount++;
            
            Serial.print("🔌 WiFi Connection attempt ");
            Serial.print(wifiRetryCount);
            Serial.println("...");
            sendDataToFlask("Status: Connection attempt " + String(wifiRetryCount) + "...");
            
            status = WiFi.begin(ssid, pass);
            
            if (status == WL_CONNECTED) {
                Serial.println("✅ WiFi Connected");
                sendDataToFlask("Status: WiFi Connected!");
                sendDataToFlask("IP:" + ipToString(WiFi.localIP()));
                if (!cameraStarted) {
                    Camera.configVideoChannel(CHANNEL, config);
                    Camera.videoInit();
                    Camera.channelBegin(CHANNEL);
                    cameraStarted = true;
                    Serial.println("🎥 Camera Initialized...");
                }
                server.begin();
                wifiConnectRequested = false;
            } else if (wifiRetryCount >= 3) {
                Serial.println("❌ WiFi Connection Failed");
                sendDataToFlask("Status: WiFi Connection Failed. Please check credentials and try again.");
                wifiConnectRequested = false;
                ssid[0] = '\0';
                pass[0] = '\0';
            }
        }
    }

    if (status == WL_CONNECTED) {
        WiFiClient client = server.available();

        if (client) {
            sendHeader(client);
            while (client.connected()) {
                Camera.getImage(CHANNEL, &img_addr, &img_len);

                char chunk_buf[64];
                uint8_t chunk_len = snprintf(chunk_buf, 64, IMG_HEADER, img_len);
                sendChunk(client, (uint8_t*)chunk_buf, chunk_len);

                sendChunk(client, (uint8_t*)img_addr, img_len);
                sendChunk(client, (uint8_t*)STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));

                delay(5); // Adjust for frame rate
            }
            client.stop();
        }
    }

    // Handle BLE Input
    if (Serial.available()) {
        String input = Serial.readString();
        sendDataToFlask(input);
    }

    delay(100);
}
