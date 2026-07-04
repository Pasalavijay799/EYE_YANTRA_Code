import sys
import builtins

_original_print = print
def safe_print(*args, **kwargs):
    encoding = sys.stdout.encoding or 'utf-8'
    new_args = []
    for arg in args:
        if isinstance(arg, str):
            try:
                arg.encode(encoding)
                new_args.append(arg)
            except UnicodeEncodeError:
                safe_str = arg.encode(encoding, errors='replace').decode(encoding)
                new_args.append(safe_str)
        else:
            new_args.append(arg)
    _original_print(*new_args, **kwargs)

builtins.print = safe_print

from flask import Flask, render_template, request, jsonify, Response,send_from_directory,send_file, redirect, url_for, session, flash
import asyncio
from bleak import BleakClient, BleakScanner
import threading
import queue
import os
import cv2
import numpy as np
import requests
from datetime import datetime
import json
import time
#from eye_detection import check_eye_status  # Import the eye detection function
import re
from results_processing import show_results  # Import the function
from HirschbergTest_Processing import HirschbergShowResult  # Import Hirschberg processing function
from eye_detection import check_eye_status  # Import eye status function
from NineGazeProcessing import process_nine_gaze_images
from process_nine_gaze_images import create_combined_image
import overallreport
from crop_eyes_from_image import crop_eyes_from_image

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    internal_path = os.path.join(base_path, "_internal", relative_path)
    if os.path.exists(internal_path):
        return internal_path
    return os.path.join(base_path, relative_path)

app = Flask(
    __name__,
    static_folder=get_resource_path('static'),
    template_folder=get_resource_path('templates')
)
app.debug = True
app.secret_key = "my_secret_key_here"

# BLE UUIDs for AMB82
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Write
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Notify

REALTEK_DEVICE_NAME = "AMEBA_BLE_DEV"

client = None
connected_device = None
is_connecting = False
received_messages = queue.Queue()
stream_ip = None  # Stores the received IP address
stream_response = None  # Global response object for the MJPEG stream

#userDetails
userName=False
personDetails={"userName":False,"dob":"","id":""}

STREAM_IP_FILE = "stream_ip.json"
UPLOAD_FOLDER = "captured_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

#testing
ble_loop = asyncio.new_event_loop()
threading.Thread(target=ble_loop.run_forever, daemon=True).start()

def schedule_ble_task(coro):
    return asyncio.run_coroutine_threadsafe(coro, ble_loop)

latest_frame = None
latest_frame_time = 0
latest_frame_lock = threading.Lock()
camera_connected = False

active_video_connections = 0
active_video_connections_lock = threading.Lock()
force_camera_active = False

STREAM_CONNECT_TIMEOUT = 5
STREAM_READ_TIMEOUT = 60
FRAME_STALE_AFTER_SECONDS = 10

# TEMP: bypass the Ameba headset IP stream and use the laptop's built-in webcam instead.
USE_LAPTOP_CAMERA = True
LAPTOP_CAMERA_INDEX = 0

def normalize_stream_ip(ip):
    if ip is None:
        return None
    ip = str(ip).strip()
    if not ip or ip.lower() == "none":
        return None
    return ip

def is_valid_ipv4(ip):
    ip = normalize_stream_ip(ip)
    if not ip:
        return False
    parts = ip.split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

def clear_latest_frame():
    global latest_frame, latest_frame_time
    with latest_frame_lock:
        latest_frame = None
        latest_frame_time = 0

def set_stream_ip(ip, persist=True):
    global stream_ip, camera_connected
    ip = normalize_stream_ip(ip)
    if ip and not is_valid_ipv4(ip):
        print(f"⚠️ Ignoring invalid stream IP: {ip}")
        return stream_ip

    if ip != stream_ip:
        print(f"🔄 Stream IP updated: {stream_ip or 'None'} -> {ip or 'None'}")
        clear_latest_frame()
        camera_connected = False

    stream_ip = ip
    if persist:
        save_stream_ip(stream_ip)
    return stream_ip

def get_latest_stream_frame():
    global force_camera_active
    # If the camera is not running because there are no active viewers,
    # temporarily activate it to grab a frame for a capture request
    if not camera_connected or latest_frame is None:
        if active_video_connections <= 0:
            print("📸 Capture requested while camera is sleeping. Temporarily waking up camera...")
            force_camera_active = True
            start_wait = time.time()
            # Wait up to 3 seconds for a valid frame to be acquired
            while time.time() - start_wait < 3.0:
                if camera_connected and latest_frame is not None:
                    break
                time.sleep(0.1)
            
            frame = None
            with latest_frame_lock:
                if latest_frame is not None and time.time() - latest_frame_time <= FRAME_STALE_AFTER_SECONDS:
                    frame = latest_frame.copy()
            
            force_camera_active = False
            return frame

    with latest_frame_lock:
        if latest_frame is None:
            return None
        if time.time() - latest_frame_time > FRAME_STALE_AFTER_SECONDS:
            return None
        return latest_frame.copy()

def stream_reader():
    global stream_ip, latest_frame, latest_frame_time, camera_connected
    current_ip = None

    # Try to pre-load the stream IP from file on startup
    try:
        with open("stream_ip.json", "r") as f:
            data = json.load(f)
            loaded_ip = normalize_stream_ip(data.get("stream_ip", None))
            if loaded_ip:
                set_stream_ip(loaded_ip, persist=False)
                print(f"🎬 Preloaded stream IP from json: {stream_ip}")
    except Exception:
        pass

    while True:
        # Stop/idle if using laptop camera or no active connections (unless temporarily forced)
        if USE_LAPTOP_CAMERA or not stream_ip or (active_video_connections <= 0 and not force_camera_active):
            camera_connected = False
            time.sleep(0.5)
            continue

        current_ip = stream_ip
        stream_url = f"http://{current_ip}:80"
        print(f"🎥 Connecting to Ameba camera stream at {stream_url}...")

        try:
            with requests.get(
                stream_url,
                stream=True,
                timeout=(STREAM_CONNECT_TIMEOUT, STREAM_READ_TIMEOUT)
            ) as response:
                if response.status_code == 200:
                    print(f"✅ Camera stream connected successfully to {current_ip}")
                    camera_connected = True
                    bytes_data = bytes()

                    for chunk in response.iter_content(chunk_size=4096):
                        # Exit stream reading if configuration changed, no viewers, or no forced capture
                        if stream_ip != current_ip or USE_LAPTOP_CAMERA or (active_video_connections <= 0 and not force_camera_active):
                            print("🔄 Stopping stream reader (config changed or no active viewers)...")
                            camera_connected = False
                            clear_latest_frame()
                            break

                        if not chunk:
                            continue

                        bytes_data += chunk

                        while True:
                            a = bytes_data.find(b'\xff\xd8') # JPEG Start
                            b = bytes_data.find(b'\xff\xd9') # JPEG End

                            if a != -1 and b != -1:
                                if a < b:
                                    jpg = bytes_data[a:b+2]
                                    bytes_data = bytes_data[b+2:]

                                    # Decode the image frame
                                    image_np = np.frombuffer(jpg, np.uint8)
                                    frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                                    if frame is not None:
                                        with latest_frame_lock:
                                            latest_frame = frame
                                            latest_frame_time = time.time()
                                else:
                                    bytes_data = bytes_data[a:]
                            else:
                                break

                    camera_connected = False
                else:
                    print(f"⚠️ Stream returned status code: {response.status_code}")
                    camera_connected = False
                    clear_latest_frame()
                    time.sleep(2)
        except Exception as e:
            print(f"❌ Error in camera stream reader: {e}")
            camera_connected = False
            clear_latest_frame()
            time.sleep(2)

WEBCAM_MAX_CONSECUTIVE_FAILURES = 10

def webcam_reader():
    """Continuously read frames from the laptop's built-in webcam when active."""
    global latest_frame, latest_frame_time, camera_connected
    cap = None
    consecutive_failures = 0

    while True:
        # Stop/release if laptop camera is not selected or no active connections (unless temporarily forced)
        if not USE_LAPTOP_CAMERA or (active_video_connections <= 0 and not force_camera_active):
            if cap is not None and cap.isOpened():
                print("🔌 Releasing laptop camera (no active viewers or switched source)...")
                cap.release()
                cap = None
            camera_connected = False
            time.sleep(0.5)
            continue

        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(LAPTOP_CAMERA_INDEX)
            if not cap.isOpened():
                print(f"❌ Could not open laptop camera (index {LAPTOP_CAMERA_INDEX}), retrying...")
                camera_connected = False
                clear_latest_frame()
                time.sleep(2)
                continue
            print(f"✅ Laptop camera (index {LAPTOP_CAMERA_INDEX}) opened successfully")
            consecutive_failures = 0

        ret, frame = cap.read()
        if not ret or frame is None:
            consecutive_failures += 1
            # A handful of transient grab failures is normal (e.g. right after
            # opening, or under brief contention) - only treat the camera as
            # disconnected once failures persist, so a fresh cached frame
            # doesn't get thrown away on a single blip.
            if consecutive_failures >= WEBCAM_MAX_CONSECUTIVE_FAILURES:
                print("⚠️ Failed to read frame from laptop camera, reconnecting...")
                camera_connected = False
                clear_latest_frame()
                cap.release()
                cap = None
                time.sleep(1)
            else:
                time.sleep(0.05)
            continue

        consecutive_failures = 0
        camera_connected = True
        with latest_frame_lock:
            latest_frame = frame
            latest_frame_time = time.time()

        time.sleep(0.03)

# Start the background camera reader threads
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    threading.Thread(target=webcam_reader, daemon=True).start()
    threading.Thread(target=stream_reader, daemon=True).start()

placeholder_frame = None

def get_placeholder_frame():
    global placeholder_frame
    if placeholder_frame is None:
        # Create a black image (480x320)
        img = np.zeros((320, 480, 3), dtype=np.uint8)
        # Fill with a beautiful dark slate background to match the glassmorphism theme
        img[:] = (35, 16, 11) # BGR for dark slate #111023
        
        # Add text: "Connecting to" and "Laptop Camera..."
        text1 = "Connecting to"
        text2 = "Laptop Camera..." if USE_LAPTOP_CAMERA else "Headset Camera..."
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Center the text
        size1 = cv2.getTextSize(text1, font, 0.7, 2)[0]
        size2 = cv2.getTextSize(text2, font, 0.7, 2)[0]
        
        x1 = (480 - size1[0]) // 2
        y1 = 140
        x2 = (480 - size2[0]) // 2
        y2 = 180
        
        cv2.putText(img, text1, (x1, y1), font, 0.7, (214, 224, 127), 2, cv2.LINE_AA) # teal/gold accent color
        cv2.putText(img, text2, (x2, y2), font, 0.7, (214, 224, 127), 2, cv2.LINE_AA)
        placeholder_frame = img
    return placeholder_frame

@app.route("/video_feed")
def video_feed():
    global active_video_connections
    with active_video_connections_lock:
        active_video_connections += 1
    print(f"🎬 Active video feed connection started. Total active: {active_video_connections}")

    def generate():
        try:
            while True:
                frame_to_send = get_latest_stream_frame()
                is_placeholder = frame_to_send is None
                if is_placeholder:
                    frame_to_send = get_placeholder_frame()

                if frame_to_send is not None:
                    ret, jpeg = cv2.imencode('.jpg', frame_to_send)
                    if ret:
                        frame_bytes = jpeg.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                               frame_bytes + b'\r\n')
                
                if is_placeholder:
                    time.sleep(0.5) # Sleep longer for placeholder to conserve resources
                else:
                    time.sleep(0.04) # ~25 fps for live stream
        finally:
            global active_video_connections
            with active_video_connections_lock:
                active_video_connections = max(0, active_video_connections - 1)
            print(f"🛑 Active video feed connection ended. Total active: {active_video_connections}")

    return Response(generate(), content_type="multipart/x-mixed-replace; boundary=frame")


'''
def add_message(message):
    global stream_ip
    if not message.strip():
        return
    print(f"📥 Received from BLE: {message}")
        except requests.exceptions.ReadTimeout:
            print(f"⏱️ Camera stream timed out after {STREAM_READ_TIMEOUT}s, reconnecting to {current_ip}...")
            camera_connected = False
            clear_latest_frame()
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"❌ Camera stream request error for {current_ip}: {e}")
            camera_connected = False
            clear_latest_frame()
            time.sleep(2)
    received_messages.put(message)

    # Capture stream IP
            clear_latest_frame()
    if message.startswith("IP:"):
        stream_ip = message[3:].strip()'''

def add_message(message):
    global stream_ip, stream_response
    if not message.strip():
        return
    print(f"📥 Received from BLE: {message}")
    received_messages.put(f"📥 Received from BLE: {message}")
    # Capture stream IP
    ip_match = re.search(r"\bIP:\s*((?:\d{1,3}\.){3}\d{1,3})", message)
    if ip_match:
        candidate_ip = ip_match.group(1)
        if is_valid_ipv4(candidate_ip):
            new_ip = set_stream_ip(candidate_ip)
            print(f"🔍 Stream IP captured: {new_ip}")
            received_messages.put(f"🔍 Stream IP captured: {new_ip}")
        else:
            print(f"⚠️ Ignoring invalid stream IP from BLE: {candidate_ip}")
            received_messages.put(f"⚠️ Invalid stream IP from BLE: {candidate_ip}")
        

@app.route("/get_stream_ip")
def get_stream_ip():
    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())
    return jsonify({
        "stream_ip": stream_ip,
        "camera_connected": camera_connected,
        "connected_device": connected_device,
        "userName": userName,
        "messages": messages
    })

@app.route("/get_connection_status")
def get_connection_status():
    return jsonify({
        "connected_device": connected_device,
        "camera_connected": camera_connected,
        "userName": userName
    })


@app.route("/get_camera_source")
def get_camera_source():
    global USE_LAPTOP_CAMERA
    return jsonify({"use_laptop_camera": USE_LAPTOP_CAMERA})


@app.route("/set_camera_source", methods=["POST"])
def set_camera_source():
    global USE_LAPTOP_CAMERA
    source = request.form.get("source")
    if source == "laptop":
        USE_LAPTOP_CAMERA = True
        clear_latest_frame()
        print("📷 Camera source set to Laptop Camera")
        return jsonify({"status": "success", "use_laptop_camera": True})
    elif source == "hardware" or source == "tablet":
        USE_LAPTOP_CAMERA = False
        clear_latest_frame()
        print(f"📷 Camera source set to {source.capitalize()} Camera")
        return jsonify({"status": "success", "use_laptop_camera": False})
    return jsonify({"status": "error", "message": "Invalid source"}), 400


@app.route("/save_manual_ip", methods=["POST"])
def save_manual_ip():
    global stream_ip
    ip = request.form.get("ip")
    if ip:
        ip = normalize_stream_ip(ip)
        if not is_valid_ipv4(ip):
            return jsonify({"status": "error", "message": "Enter a valid camera IP address"}), 400
        set_stream_ip(ip)
        print(f"✏️ Manually saved stream IP: {stream_ip}")
        return jsonify({"status": "success", "ip": stream_ip})
    return jsonify({"status": "error", "message": "IP cannot be empty"}), 400


async def scan_devices():
    try:
        devices = await BleakScanner.discover()
        return [(device.name, device.address) for device in devices if device.name == REALTEK_DEVICE_NAME]
    except Exception as e:
        print(f"❌ BLE Scan Error: {e}")
        received_messages.put(f"❌ BLE Scan Error: {e}")
        return []


# def notification_handler(sender, data):
#     try:
#         message = data.decode("utf-8",errors="ignore")
#         add_message(message)
#     except Exception as e:
#         print(f"❌ Error decoding BLE message: {e}")

#testing
# AMB82 notifications are capped at 20 bytes per packet, so a single logical
# message arrives as several chunks terminated by '\n'. Buffer chunks here and
# only hand complete, newline-delimited messages to add_message().
notify_buffer = ""

def global_notification_handler(sender, data):
    global notify_buffer
    try:
        notify_buffer += data.decode("utf-8", errors="ignore")
        while "\n" in notify_buffer:
            msg, notify_buffer = notify_buffer.split("\n", 1)
            print(f"📥 [BLE Notify] {msg}")
            add_message(msg)
    except Exception as e:
        print(f"❌ [BLE Notify] Decode error: {e}")
        print(f"🔍 Raw data: {data.hex()}")


# async def connect_to_realtek(address):
#     global client, connected_device

#     print(f"🔗 Connecting to {address}")
#     client = BleakClient(address)

#     try:
#         await client.connect()
#         connected_device = address
#         print(f"✅ Connected to {address}")

#         await client.start_notify(CHARACTERISTIC_UUID_TX, notification_handler)
#         print("🔔 Notifications enabled!")

#         while clyient.is_connected:
#             await asyncio.sleep(0.5)

#     except Exception as e:
#         print(f"❌ Connection error: {e}")
#     finally:
#         print("❌ BLE Disconnected")
#         connected_device = None

#testing
async def connect_and_store_client(address):
    global client, connected_device, is_connecting, notify_buffer

    if is_connecting or connected_device == address:
        return

    is_connecting = True
    max_attempts = 3
    connected = False
    notify_buffer = "" # discard any partial chunk left over from a previous connection

    try:
        for attempt in range(1, max_attempts + 1):
            print(f"🔗 [BLE] Connecting to {address} (attempt {attempt}/{max_attempts})...")

            # Clean up any stale client before retrying so BlueZ doesn't wedge on the address
            if client is not None:
                try:
                    if client.is_connected:
                        await client.disconnect()
                except Exception:
                    pass

            client = BleakClient(address, timeout=20.0)

            try:
                await client.connect()
                connected = True
                connected_device = address
                print(f"✅ [BLE] Connected to {address}")
                received_messages.put(f"✅ [BLE] Connected to {address}")

                await client.start_notify(CHARACTERISTIC_UUID_TX, global_notification_handler)
                print("🔔 [BLE] Notifications enabled")
                received_messages.put("🔔 [BLE] Notifications enabled")
                break
            except Exception as e:
                print(f"❌ [BLE] Connection error (attempt {attempt}/{max_attempts}): {repr(e)}")
                received_messages.put(f"❌ [BLE] Connection error (attempt {attempt}/{max_attempts}): {repr(e)}")
                if attempt < max_attempts:
                    await asyncio.sleep(2)

        if not connected:
            return

        is_connecting = False
        while client.is_connected:
            await asyncio.sleep(0.5)
    finally:
        print(f"❌ [BLE] Connection closed for {address}")
        received_messages.put("❌ [BLE] Connection closed")
        connected_device = None
        is_connecting = False

async def send_ble_message(message):
    if client and client.is_connected:
        try:
            full_msg = message + "\n"
            encoded_msg = full_msg.encode('utf-8')
            chunk_size = 20
            for i in range(0, len(encoded_msg), chunk_size):
                chunk = encoded_msg[i:i+chunk_size]
                await client.write_gatt_char(CHARACTERISTIC_UUID_RX, chunk)
                await asyncio.sleep(0.1)  # Brief delay to allow the device to process the packet
            print(f"📤 Sent to BLE in chunks: {message}")
            received_messages.put(f"📤 Sent: {message}")
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            received_messages.put(f"❌ Failed to send: {e}")
    else:
        print("❌ No BLE connection available.")
        received_messages.put("❌ No BLE connection available.")


# @app.route("/", methods=["GET", "POST"])
# def index():
#     global connected_device, stream_ip

#     if request.method == "POST":
#         if "address" in request.form:
#             address = request.form.get("address")
#             name = request.form.get("name")

#             if name == REALTEK_DEVICE_NAME:
#                 #threading.Thread(target=lambda: asyncio.run(connect_to_realtek(address))).start()
#                 asyncio.run_coroutine_threadsafe(connect_and_store_client(address), ble_loop)
#             else:
#                 received_messages.put("❌ Not a Realtek IoT Camera.")

#         elif "ssid" in request.form and "password" in request.form and connected_device:
#             ssid = request.form.get("ssid")
#             password = request.form.get("password")
#             wifi_credentials = f"{ssid},{password}"
#             threading.Thread(target=lambda: asyncio.run(send_ble_message(wifi_credentials))).start()

#     devices = asyncio.run(scan_devices())

#     messages = []
#     # print(received_messages)
#     while not received_messages.empty():
#         messages.append(received_messages.get())

#     return render_template("index.html", devices=devices, connected=connected_device, messages=messages, stream_ip=stream_ip)

@app.route("/", methods=["GET", "POST"])
def index():
    global connected_device, stream_ip, userName, personDetails
    print(userName)
    print(request.path, request.endpoint)
   
    if request.method == "POST":
        print(request.form)
        if "patient_name" in request.form:
            patient_name = request.form.get("patient_name", "").strip()
            if patient_name == "":
                received_messages.put("UserName Required*")
            else:
                personDetails["userName"] = patient_name
                personDetails["dob"] = request.form.get("patient_dob", "")
                personDetails["id"] = request.form.get("patient_id", "")
                raw_user_name = f'{personDetails["userName"]}_{personDetails["id"]}_{personDetails["dob"]}'
                userName = re.sub(r'[\\/*?:"<>|]', '_', raw_user_name)
                print("Login successful. Opening Bluetooth page...")
                return redirect(url_for("bluetooth"))
        
        elif "address" in request.form:
            address = request.form.get("address")
            name = request.form.get("name")
            print(f"🔗 [BLE] Received request to connect to {name} ({address})")
            set_stream_ip(None)
            schedule_ble_task(connect_and_store_client(address))
            return redirect(url_for("bluetooth"))

        elif "ssid" in request.form and "password" in request.form and connected_device:
            ssid = request.form.get("ssid")
            password = request.form.get("password")
            wifi_credentials = f"{ssid},{password}"
            set_stream_ip(None)
            schedule_ble_task(send_ble_message(wifi_credentials))
            return redirect(url_for("bluetooth"))

    return redirect(url_for("admin_page"))


@app.route("/intake", methods=["GET"])
def intake():
    global connected_device, stream_ip, userName, personDetails
    
    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())
        
    return render_template(
        "index.html",
        devices=[],
        connected=connected_device,
        messages=messages,
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails
    )

@app.route("/bluetooth")
def bluetooth():
    global connected_device, stream_ip, userName, personDetails

    auto_connecting_to = None
    if connected_device:
        devices = []
    elif is_connecting:
        devices = []
        auto_connecting_to = REALTEK_DEVICE_NAME
    else:
        devices = asyncio.run(scan_devices())
        if devices:
            name, address = devices[0]
            print(f"🔗 [BLE] Found {name} ({address}), auto-connecting...")
            schedule_ble_task(connect_and_store_client(address))
            auto_connecting_to = name
            devices = []

    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())

    return render_template(
        "index2.html",
        devices=devices,
        connected=connected_device,
        auto_connecting=auto_connecting_to,
        messages=messages,
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails
    )

@app.route("/dashboard")
def dashboard():
    global connected_device, stream_ip, userName, personDetails
    
    prelim_status = False
    hirschberg_status = False
    nine_gaze_status = False
    
    if userName:
        import glob
        # Check Preliminary Results
        prelim_files = glob.glob(os.path.join("Preliminary_Results", f"{userName}*.jpg"))
        if prelim_files:
            prelim_status = True
        
        # Check Hirschberg Results
        hirsch_files = glob.glob(os.path.join("Hirschberg_Results", f"processed_hirschberg_{userName}*.jpg"))
        if hirsch_files:
            hirschberg_status = True
            
        # Check 9Gaze Results
        gaze_folder = os.path.join("9GazeResults", f"{userName}_*Areal")
        gaze_dirs = glob.glob(gaze_folder)
        if gaze_dirs:
            nine_gaze_status = True

    return render_template(
        "dashboard.html",
        userName=userName,
        personDetails=personDetails,
        connected=connected_device,
        stream_ip=stream_ip,
        prelim_status=prelim_status,
        hirschberg_status=hirschberg_status,
        nine_gaze_status=nine_gaze_status
    )

@app.route("/report")
def report_page():
    global connected_device, stream_ip, userName, personDetails
    return render_template(
        "report.html",
        userName=userName,
        personDetails=personDetails,
        connected=connected_device,
        stream_ip=stream_ip
    )

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/working_process")
def working_process():
    return render_template("working_process.html")

@app.route("/reset_app")
def reset_app():
    global client,connected_device,stream_ip,stream_response,userName
    client = None
    connected_device = None
    set_stream_ip(None)
    stream_response = None  # Global response object for the MJPEG stream
    userName=False
    return redirect(url_for("index"))


'''
@app.route("/capture", methods=["POST"])
def capture():
    global stream_ip

    if not stream_ip:
        return jsonify({"message": "❌ No stream available."}), 400

    name = request.form.get("name")
    date = request.form.get("date")

    if not name or not date:
        return jsonify({"message": "❌ Name and date required."}), 400

    # Fetch an image from the MJPEG stream
    stream_url = f"http://{stream_ip}:80"
    try:
        response = requests.get(stream_url, stream=True)
        if response.status_code == 200:
            bytes_data = bytes()
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')  # Start of JPEG
                b = bytes_data.find(b'\xff\xd9')  # End of JPEG
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    image_np = np.frombuffer(jpg, np.uint8)
                    frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                    break
        else:
            return jsonify({"message": "❌ Failed to fetch image."}), 500
    except Exception as e:
        return jsonify({"message": f"❌ Error fetching image: {e}"}), 500

    # Overlay text on the image
    text = f"{name} - {date}"
    cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Save image
    filename = os.path.join(UPLOAD_FOLDER, f"captured_{name}_{date}.jpg")
    cv2.imwrite(filename, frame)

    return jsonify({"message": f"✅ Image saved as {filename}"}), 200
'''

def save_stream_ip(ip):
    """Save the IP address to a file."""
    with open(STREAM_IP_FILE, "w") as f:
        json.dump({"stream_ip": normalize_stream_ip(ip)}, f)

def load_stream_ip():
    """Load the IP address from the file if it exists."""
    global stream_ip
    try:
        with open(STREAM_IP_FILE, "r") as f:
            data = json.load(f)
            set_stream_ip(data.get("stream_ip", None), persist=False)
    except (FileNotFoundError, json.JSONDecodeError):
        set_stream_ip(None, persist=False)  # Default to None if file not found or invalid

#load_stream_ip()
@app.route("/capture", methods=["POST"])
def capture():
    global userName  # Keep track of the user
    print(f"🔍 Debug: Capturing from cached stream frame")

    if not USE_LAPTOP_CAMERA:
        load_stream_ip()
        if not stream_ip or stream_ip.lower() == "none":
            return jsonify({"message": "No stream available.","status":"error"}), 400

    name = userName
    date = request.form.get("date")

    if not name or not date:
        return jsonify({"message": "Name and date required.","status":"error"}), 400

    try:
        frame = get_latest_stream_frame()

        if frame is None:
            return jsonify({"message": "Camera stream is not live yet. Please wait for the camera to reconnect.","status":"error"}), 500

        # 📝 Overlay name & date on image
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 💾 Save image
        filename = os.path.join(UPLOAD_FOLDER, f"captured_{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(filename):
                os.remove(filename)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry
        
        crop_eyes_from_image(filename)

        return jsonify({"message": f"Image saved as {filename}","status":"success"}), 200

    except Exception as e:
        return jsonify({"message": f"Error capturing image: {e}","status":"error"}), 500





#route for preliminary
#load_stream_ip()
@app.route("/preliminary")
def preliminary_test():
    global stream_ip, userName, personDetails, connected_device
    return render_template(
        "preliminary.html",
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails,
        connected=connected_device
    )

# Create a folder for preliminary captures
PRELIMINARY_FOLDER = "preliminary"
os.makedirs(PRELIMINARY_FOLDER, exist_ok=True)  # Ensure the folder exists

@app.route("/preliminaryroute", methods=["POST"])
def preliminary_capture():
    print(f"🔍 Debug: Capturing preliminary from cached frame")

    if not USE_LAPTOP_CAMERA:
        load_stream_ip()
        if not stream_ip or stream_ip.lower() == "none":
            return jsonify({"message": "❌ No stream available.","status":"error"}), 400

    name = userName
    date = request.form.get("date")

    if not name:
        return jsonify({"message": "❌ Name is required.","status":"error"}), 400

    if not date:
        date = datetime.today().strftime('%Y-%m-%d')  # Auto-fill date

    try:
        frame = get_latest_stream_frame()

        if frame is None:
            return jsonify({"message": "Camera stream is not live yet. Please wait for the camera to reconnect.","status":"error"}), 500

        # 📝 Overlay name & date
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 💾 Save image in the "preliminary" folder with new format `{name}_{date}.jpg`
        filename = os.path.join(PRELIMINARY_FOLDER, f"{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(filename):
                os.remove(filename)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry
        
        #crop_eyes_from_image(filename)

        # Proactively run eye analysis so processed files exist for report generation
        try:
            processed_filename = f"{name}_{date}.jpg"
            processed_path = os.path.join("Preliminary_Results", processed_filename)
            from results_processing import analyze_eyes
            analyze_eyes(frame.copy(), processed_path, processed_filename)
            print(f"✅ Proactively processed preliminary image for {name}")
        except Exception as pe:
            print(f"⚠️ Proactive preliminary processing failed: {pe}")

        # ✅ Redirect to preliminary test page
        return jsonify({"message": f"Image saved as {filename}","status":"success"}), 200

    except Exception as e:
        return jsonify({"message": f"Error capturing image: {e}","status":"error"}), 500



# results for preliminary test
PreliminaryResults_Folder = "Preliminary_Results"
os.makedirs(PreliminaryResults_Folder, exist_ok=True)  # Ensure results folder exists
'''
@app.route("/results")
def show_results():
    try:
         # Get the latest image from the preliminary folder based on modification time
        images = [f for f in os.listdir(PRELIMINARY_FOLDER) if f.endswith((".jpg", ".png"))]
        if not images:
            return "❌ No images found.", 404

        latest_image = max(images, key=lambda f: os.path.getmtime(os.path.join(PRELIMINARY_FOLDER, f)))
          
        image_path = os.path.join(PRELIMINARY_FOLDER, latest_image)

        # Load image and apply processing (Example: Convert to grayscale)
        frame = cv2.imread(image_path)
        processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  

        # Save processed image
        processed_filename = f"processed_{latest_image}"
        processed_path = os.path.join(PreliminaryResults_Folder, processed_filename)
        cv2.imwrite(processed_path, processed_frame)

        # Create text file with details
        text_filename = processed_filename.replace(".jpg", ".txt")
        text_path = os.path.join(PreliminaryResults_Folder, text_filename)

        with open(text_path, "w") as file:
            file.write(f"Processed Image: {processed_filename}\n")
            file.write(f"Original Image: {latest_image}\n")
            file.write("Processing: Grayscale conversion\n")

        # Render results page
        return render_template("Preliminary_Results.html", processed_image=processed_filename, text_filename=text_filename)


    except Exception as e:
        return f"❌ Error processing image: {e}", 500'''


'''
@app.route("/results")
def show_results():
    try:
        # Get the latest image based on modification time
        images = sorted(
            [f for f in os.listdir(PRELIMINARY_FOLDER) if f.endswith((".jpg", ".png"))],
            key=lambda f: os.path.getmtime(os.path.join(PRELIMINARY_FOLDER, f))
        ,reverse=True)  # Sort in descending order

        if not images:
             session["error_message"] = "❌ No images found. Please capture an image first."
             return redirect(url_for("preliminary_test"))

        latest_image = images[0]
        image_path = os.path.join(PRELIMINARY_FOLDER, latest_image)

        # Check eye status
        eye_status = check_eye_status(image_path)
        print(f"🔍 Eye status: {eye_status}"  )
        if "⚠️" in eye_status:
            session["error_message"] = eye_status  # Store the error message
            return redirect(url_for("preliminary_test"))  # Redirect to capture page

        # Load image for processing
        image = cv2.imread(image_path)
        if image is None:
            session["error_message"] = "❌ Could not load image. Please try again."
            return redirect(url_for("preliminary_test"))

        # Convert to grayscale
        processed_frame = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Save processed image
        processed_filename = f"{latest_image}"
        processed_path = os.path.join(PreliminaryResults_Folder, processed_filename)
        cv2.imwrite(processed_path, processed_frame)

        # Create text file with details
        text_filename = processed_filename.replace(".jpg", ".txt").replace(".png", ".txt")
        text_path = os.path.join(PreliminaryResults_Folder, text_filename)

        with open(text_path, "w") as file:
            file.write(f"Processed Image: {processed_filename}\n")
            file.write(f"Original Image: {latest_image}\n")
            file.write("Processing: Grayscale conversion\n")

        return render_template(
            "Preliminary_Results.html",
            status="success",
            message="✅ Eyes detected as open, proceeding to results.",
            processed_image=processed_filename,
            text_file=text_filename
        )

    except Exception as e:
         session["error_message"] = f"❌ Error: {str(e)}"
         return redirect(url_for("preliminary_test"))

'''

@app.route("/results")
def results_page():
    global userName, personDetails, connected_device
    return show_results(userName=userName, personDetails=personDetails, connected_device=connected_device)

'''

@app.route("/download/image/<filename>")
def download_image(filename):
    try:
        file_path = os.path.join(PreliminaryResults_Folder, filename)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return "❌ Processed image not found.", 404

        print(f"✅ Serving processed image: {file_path}")
        return send_file(file_path, mimetype="image/jpeg")

    except Exception as e:
        print(f"❌ Error serving image: {e}")
        return f"❌ Error serving image: {e}", 500


@app.route("/download/text/<filename>")
def download_text(filename):
    try:
        file_path = os.path.join(PreliminaryResults_Folder, filename)

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return "❌ Processed text file not found.", 404

        print(f"✅ Serving processed text file: {file_path}")
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        print(f"❌ Error serving text file: {e}")
        return f"❌ Error serving text file: {e}", 500'''
    

#download for both preliminary and hirschberg test
@app.route("/download/<test_type>/image/<filename>")
def download_image(test_type, filename):
    try:
        # Determine the folder based on the test type
        if test_type == "preliminary":
            folder = "Preliminary_Results"
        elif test_type == "hirschberg":
            folder = "Hirschberg_Results"
        else:
            return "❌ Invalid test type!", 400  # Return error for unknown test types

        file_path = os.path.abspath(os.path.join(folder, filename))

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return "❌ Processed image not found.", 404

        print(f"✅ Serving processed image: {file_path}")
        return send_file(file_path, mimetype="image/jpeg")

    except Exception as e:
        print(f"❌ Error serving image: {e}")
        return f"❌ Error serving image: {e}", 500


@app.route("/download/<test_type>/text/<filename>")
def download_text(test_type, filename):
    try:
        # Determine the folder based on the test type
        if test_type == "preliminary":
            folder = "Preliminary_Results"
        elif test_type == "hirschberg":
            folder = "Hirschberg_Results"
        else:
            return "❌ Invalid test type!", 400  # Return error for unknown test types

        file_path = os.path.abspath(os.path.join(folder, filename))
        print(f"🔍 Debug: File path = {file_path}")

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return "❌ Processed text file not found.", 404

        print(f"✅ Serving processed text file: {file_path}")
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        print(f"❌ Error serving text file: {e}")
        return f"❌ Error serving text file: {e}", 500



#Hirschberg test routes

HIRSCHBERG_RESULTS_FOLDER = "HirschbergTestImages"
if not os.path.exists(HIRSCHBERG_RESULTS_FOLDER):
    os.makedirs(HIRSCHBERG_RESULTS_FOLDER)


import time
@app.route("/hirschberg", methods=["GET"])
def hirschberg_test():
    """Render the Hirschberg test page."""
    global stream_ip, userName, personDetails, connected_device
    # Ensure stream IP is loaded
    if not USE_LAPTOP_CAMERA:
        load_stream_ip()
        if not stream_ip or stream_ip.lower() == "none":
            return jsonify({"message": "❌ No stream available.","status":"error"}), 400

    return render_template(
        "hirschbergTest.html",
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails,
        connected=connected_device,
        use_laptop_camera=USE_LAPTOP_CAMERA
    )

async def send_ble_command(command, expected_response, timeout=100000):
    """Send BLE command and wait for the expected response."""
    print("send_ble_command: 1")
    global client
    if not client or not client.is_connected:
        return False

    received = None
    print("send_ble_command: 2")

    # def notification_handler(sender, data):
    #     nonlocal received
    #     try:
    #         received = data.decode("utf-8", errors="ignore")  # Ignore invalid bytes
    #         print(f"📥 BLE Response: {received}")
    #     except Exception as e:
    #         print(f"❌ Failed to decode notification: {e}")
    #         print(f"🔍 Raw data: {data.hex()}")


    print("send_ble_command: 3")
    await client.start_notify(CHARACTERISTIC_UUID_TX, global_notification_handler)
    print("send_ble_command: 4")
    await client.write_gatt_char(CHARACTERISTIC_UUID_RX, (command + "\n").encode())
    # if command == "LightOn":
    #     await client.write_gatt_char(CHARACTERISTIC_UUID_RX, bytearray([0x01]))
    # elif command == "LightOff":
    #     await client.write_gatt_char(CHARACTERISTIC_UUID_RX, bytearray([0x00]))
    # else:
    #     await client.write_gatt_char(CHARACTERISTIC_UUID_RX, command.encode())
    print("send_ble_command: 5")
    return True

    # start_time = time.time()
    # while time.time() - start_time < timeout:
    #     print(f"inside {time.time()}")
    #     if received and expected_response in received:
    #         await client.stop_notify(CHARACTERISTIC_UUID_TX)
    #         return True
    #     await asyncio.sleep(0.5)
    # print("send_ble_command: 6")
    # await client.stop_notify(CHARACTERISTIC_UUID_TX)
    # print("send_ble_command: 7")
    # return False

@app.route("/hirschberg_capture", methods=["POST"])
def capture_hirschberg_image():
    """Handles capturing an image for the Hirschberg test."""
    global stream_ip, userName

    print(f"🔍 Debug: Capturing Hirschberg test from cached stream frame")

    if not USE_LAPTOP_CAMERA and (not stream_ip or stream_ip.lower() == "none"):
        return jsonify({"message": "No stream available.","status":"error"}), 400

    name = userName
    date = request.form.get("date")

    if not name or not date:
        return jsonify({"message": "Name and date required.","status":"error"}), 400

    # Step 1: Send LightOn command via BLE and wait for confirmation if using headset
    if not USE_LAPTOP_CAMERA:
        future = schedule_ble_task(send_ble_command("LightOn", "LightOn", timeout=60))
        success = future.result()  # Optional timeout to avoid hanging
        print("success", success)

        if not success:
            return jsonify({"message": "Failed to turn on light.","status":"error"}), 500
    else:
        # Allow time for front screen flash to fully render and light up face
        time.sleep(0.5)

    # Wait briefly for the LED light to be captured in the video stream frames
    time.sleep(0.3)

    try:
        # Step 2: Capture the last frame from the stream proxy buffer
        frame = get_latest_stream_frame()

        if frame is None:
            return jsonify({"message": "Camera stream is not live yet. Please wait for the camera to reconnect.","status":"error"}), 500

        # Step 3: Overlay name & date on image
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Step 4: Save image
        filename = os.path.join(HIRSCHBERG_RESULTS_FOLDER, f"hirschberg_{name}_{date}.jpg")
        cv2.imwrite(filename, frame)
        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(filename):
                os.remove(filename)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry
        #crop_eyes_from_image(filename)
        # Proactively run Hirschberg analysis so processed files exist for report generation
        try:
            # HirschbergShowResult flips the image before processing (cv2.flip(image, 1))
            # Let's match that behavior exactly
            flipped_frame = cv2.flip(frame, 1)
            from hirschberg_analysis import analyze_hirschberg
            analyze_hirschberg(flipped_frame, "Hirschberg_Results", f"hirschberg_{name}_{date}.jpg")
            print(f"✅ Proactively processed Hirschberg image for {name}")
        except Exception as he:
            print(f"⚠️ Proactive Hirschberg processing failed: {he}")
        print("after capturing frame in hirschberg test image")

    except Exception as e:
        return jsonify({"message": f"Error capturing image: {e}","status":"error"}), 500

    # Step 5: Send LightOff command via BLE and wait for confirmation if using headset
    if not USE_LAPTOP_CAMERA:
        try:
            future = schedule_ble_task(send_ble_command("LightOff", "LightOff", timeout=60))
            success = future.result()
        except Exception as e:
            print(f"❌ LightOff command failed: {e}")
            success = False

        # Optional retry
        if not success:
            print("🔁 Retrying LightOff command...")
            try:
                future = schedule_ble_task(send_ble_command("LightOff", "LightOff", timeout=60))
                success = future.result()
            except Exception as e:
                print(f"❌ Retry LightOff command failed: {e}")
                success = False

        if not success:
            return jsonify({"message": "LightOff command did not receive confirmation.","status":"error"}), 500

    return jsonify({"message": f"Hirschberg Image saved as {filename}","status":"success"}), 200









@app.route("/hirschberg_results")
def hirschberg_results():
    global userName, personDetails, connected_device
    return HirschbergShowResult(userName=userName, personDetails=personDetails, connected_device=connected_device)




#routes for 9Gaze test

# Folder for storing 9 gaze images
GAZE_TEST_FOLDER = "9GazeTestImages"
if not os.path.exists(GAZE_TEST_FOLDER):
    os.makedirs(GAZE_TEST_FOLDER)


@app.route("/9gaze")
def nine_gaze_test():
    global stream_ip, userName, personDetails, connected_device
    return render_template(
        "9gaze.html",
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails,
        connected=connected_device
    )

'''
@app.route("/capture_9gaze", methods=["POST"])
def capture_9gaze():
    global stream_ip
    print(f"🔍 Debug: Capturing 9 Gaze Test from {stream_ip}")

    if not stream_ip or stream_ip.lower() == "none":
        return jsonify({"message": "❌ No stream available."}), 400

    name = request.form.get("name")
    gaze_position = request.form.get("gaze")

    if not name or not gaze_position:
        return jsonify({"message": "❌ Name and gaze position required."}), 400

    try:
        # Capture the last frame from the stream
        stream_url = f"http://{stream_ip}:80"
        response = requests.get(stream_url, stream=True)

        bytes_data = bytes()
        frame = None  

        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')  # Start of JPEG
            b = bytes_data.find(b'\xff\xd9')  # End of JPEG
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                image_np = np.frombuffer(jpg, np.uint8)
                frame = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                break

        if frame is None:
            return jsonify({"message": "❌ Could not decode image."}), 500

        # Save the image
        person_folder = os.path.join(GAZE_TEST_FOLDER, name)
        if not os.path.exists(person_folder):
            os.makedirs(person_folder)

        image_filename = f"gaze_{gaze_position}.jpg"
        image_path = os.path.join(person_folder, image_filename)
        cv2.imwrite(image_path, frame)

        return jsonify({"message": f"✅ Image saved: {image_filename}"})

    except Exception as e:
        return jsonify({"message": f"❌ Error: {str(e)}"}), 500

'''


@app.route("/capture_9gaze", methods=["POST"])
def capture_9gaze():
    global stream_ip, userName
    print(f"🔍 Debug: Capturing 9 Gaze Test from cached stream frame")

    if not USE_LAPTOP_CAMERA and (not stream_ip or stream_ip.lower() == "none"):
        return jsonify({"message": "No stream available.","status":"error"}), 400

    name = userName

    #adding date to the name
    date = datetime.today().strftime('%Y-%m-%d')  # Auto-fill date
    name=f"{name}_{date}"

    gaze_position = request.form.get("gaze")

    if not name or not gaze_position:
        return jsonify({"message": "Name and gaze position required.","status":"error"}), 400

    try:
        # Capture the last frame from the stream proxy buffer
        frame = get_latest_stream_frame()

        if frame is None:
            return jsonify({"message": "Camera stream is not live yet. Please wait for the camera to reconnect.","status":"error"}), 500

        # Save the temporary image for checking eye status
        temp_image_path = "temp_gaze.jpg"
        cv2.imwrite(temp_image_path, frame)

        # Check if eyes are open
        eye_status = check_eye_status(temp_image_path)
        print(f"🔍 Eye status: {eye_status}")
        if "closed" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry

        # Save the final image
        person_folder = os.path.join(GAZE_TEST_FOLDER, name)
        if not os.path.exists(person_folder):
            os.makedirs(person_folder)

        image_filename = f"gaze_{gaze_position}.jpg"
        image_path = os.path.join(person_folder, image_filename)
        cv2.imwrite(image_path, frame)

        #crop_eyes_from_image(image_path)

        return jsonify({"message": f"Image saved: {image_filename}", "retry": False,"status":"success"})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}","status":"error"}), 500





#9gaze results route

# @app.route("/9gaze_results")
# def nine_gaze_results():
#     name = request.args.get("name")

#     if not name:
#         return "❌ Name parameter is missing.", 400

#     person_folder = os.path.join(GAZE_TEST_FOLDER, name)

#     if not os.path.exists(person_folder):
#         return f"❌ No gaze test data found for {name}.", 404

#     # Get the list of captured gaze images (1 to 9)
#     captured_images = []
#     for i in range(1, 10):  
#         image_path = f"gaze_{i}.jpg"
#         if os.path.exists(os.path.join(person_folder, image_path)):
#             captured_images.append(image_path)

#     # Ensure all 9 images exist
#     if len(captured_images) < 9:
#         missing = 9 - len(captured_images)
#         return f"⚠️ Only {len(captured_images)}/9 images found. {missing} images missing.", 400
#      # Fetch processed images and areal ratios file
#     processed_images = [f for f in os.listdir(processed_folder) if f.endswith(".jpg")]
#     text_file = "areal_ratios.txt" if os.path.exists(os.path.join(processed_folder, "areal_ratios.txt")) else None

#     return render_template("9gaze_results.html", name=name, images=processed_images, text_file=text_file)




@app.route("/9gaze_results", methods=["GET"])
def view_9gaze_results():
    name = request.args.get("name")
    if not name:
        return "❌ Name parameter is required.", 400

    #adding date to the name    
    date = datetime.today().strftime('%Y-%m-%d')  # Auto-fill date
    name=f"{name}_{date}"

    gaze_folder = "9GazeTestImages"
    output_folder = "9GazeResults"

    person_folder = os.path.join(gaze_folder, name)
    processed_folder = os.path.join(output_folder, f"{name}_Areal")

    if not os.path.exists(person_folder):
        return "❌ No images found for this person.", 400

    captured_images = [f for f in os.listdir(person_folder) if f.startswith("gaze_") and f.endswith(".jpg")]

    if len(captured_images) < 9:
        missing = 9 - len(captured_images)
        return f"⚠️ Only {len(captured_images)}/9 images found. {missing} images missing.", 400

    # Perform the 9 gaze analysis
    result_message, status_code = process_nine_gaze_images(name, gaze_folder, output_folder)
    if status_code != 200:
        return result_message, status_code
    # Generate the combined image
    combined_image_filename = create_combined_image(name, output_folder)

    # Fetch processed images and areal ratios file
    processed_images = [f for f in os.listdir(processed_folder) if f.endswith(".jpg") and f != "combined_9gaze.jpg"]
    text_file = "areal_ratios.txt" if os.path.exists(os.path.join(processed_folder, "areal_ratios.txt")) else None

    global userName, personDetails, connected_device
    return render_template(
        "9gaze_results.html",
        name=name,
        images=processed_images,
        text_file=text_file,
        combined_image=combined_image_filename,
        userName=userName,
        personDetails=personDetails,
        connected=connected_device
    )




@app.route("/9gaze_results/<name>/<filename>")
def serve_9gaze_file(name, filename):
    output_folder = "9GazeResults"
    
    #adding date to the name
    # date = datetime.today().strftime('%Y-%m-%d')  # Auto-fill date
    # name=f"{name}_{date}"
    
    processed_folder = os.path.abspath(os.path.join(output_folder, f"{name}_Areal"))

    if not os.path.exists(os.path.join(processed_folder, filename)):
        return "❌ File not found.", 404

    return send_from_directory(processed_folder, filename)


@app.route("/generate_overall_report", methods=["GET"])
def generate_overall_report():
    global personDetails
    try:
        # Fallback processing check: Ensure files are processed for the current user
        p_name = personDetails.get('userName', '')
        if isinstance(p_name, bool):
            p_name = "False" if p_name else ""
        p_id = str(personDetails.get('id', ''))
        p_dob = str(personDetails.get('dob', ''))
        user_str = f"{p_name}_{p_id}_{p_dob}" if p_name else ""
        
        # 1. Fallback for Preliminary:
        import glob
        if user_str:
            prelim_raw_files = glob.glob(os.path.join("preliminary", f"*{user_str}*.jpg"))
        else:
            prelim_raw_files = glob.glob(os.path.join("preliminary", "*.jpg"))

        if prelim_raw_files:
            latest_raw = max(prelim_raw_files, key=os.path.getctime)
            basename = os.path.basename(latest_raw)
            processed_path = os.path.join("Preliminary_Results", basename)
            if not os.path.exists(processed_path):
                print(f"🔄 Fallback processing preliminary image for {basename}...")
                raw_img = cv2.imread(latest_raw)
                if raw_img is not None:
                    from results_processing import analyze_eyes
                    try:
                        analyze_eyes(raw_img, processed_path, basename)
                    except Exception as pe:
                        print(f"⚠️ Fallback preliminary processing failed for {basename}: {pe}")
                    
        # 2. Fallback for Hirschberg:
        if user_str:
            hirsch_raw_files = glob.glob(os.path.join("HirschbergTestImages", f"*hirschberg_{user_str}*.jpg"))
            if not hirsch_raw_files:
                hirsch_raw_files = glob.glob(os.path.join("HirschbergTestImages", f"*{user_str}*.jpg"))
        else:
            hirsch_raw_files = glob.glob(os.path.join("HirschbergTestImages", "*.jpg"))

        if hirsch_raw_files:
            latest_raw = max(hirsch_raw_files, key=os.path.getctime)
            basename = os.path.basename(latest_raw)
            processed_path = os.path.join("Hirschberg_Results", f"processed_{basename}")
            if not os.path.exists(processed_path):
                print(f"🔄 Fallback processing Hirschberg image for {basename}...")
                raw_img = cv2.imread(latest_raw)
                if raw_img is not None:
                    flipped_img = cv2.flip(raw_img, 1)
                    from hirschberg_analysis import analyze_hirschberg
                    try:
                        analyze_hirschberg(flipped_img, "Hirschberg_Results", basename)
                    except Exception as he:
                        print(f"⚠️ Fallback Hirschberg processing failed for {basename}: {he}")

        # 3. Fallback for 9-Gaze:
        gaze_output_folder = "9GazeResults"
        if user_str:
            gaze_processed_dirs = glob.glob(os.path.join(gaze_output_folder, f"*{user_str}*_Areal"))
        else:
            gaze_processed_dirs = glob.glob(os.path.join(gaze_output_folder, "*_Areal"))

        if not gaze_processed_dirs:
            if user_str:
                gaze_raw_dirs = glob.glob(os.path.join("9GazeTestImages", f"*{user_str}*"))
            else:
                gaze_raw_dirs = glob.glob(os.path.join("9GazeTestImages", "*"))
                gaze_raw_dirs = [d for d in gaze_raw_dirs if os.path.isdir(d)]

            if gaze_raw_dirs:
                latest_raw_dir = max(gaze_raw_dirs, key=os.path.getctime)
                folder_name = os.path.basename(latest_raw_dir)
                raw_imgs = [f for f in os.listdir(latest_raw_dir) if f.startswith("gaze_") and f.endswith(".jpg")]
                if len(raw_imgs) >= 9:
                    print(f"🔄 Fallback processing 9-Gaze for {folder_name}...")
                    from NineGazeProcessing import process_nine_gaze_images
                    from process_nine_gaze_images import create_combined_image
                    try:
                        process_nine_gaze_images(folder_name, "9GazeTestImages", gaze_output_folder)
                        create_combined_image(folder_name, gaze_output_folder)
                    except Exception as ge:
                        print(f"⚠️ Fallback 9-Gaze processing failed for {folder_name}: {ge}")

        pdf_path, pattern_result = overallreport.generate_pdf_report(personDetails=personDetails)
        return jsonify({"status": "success", "pattern": pattern_result})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/download_overall_report", methods=["GET"])
def download_overall_report():
    pdf_path = os.path.abspath("Overall_Report.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return "❌ Report not found.", 404


@app.route("/admin", methods=["GET"])
def admin_page():
    global connected_device, stream_ip, userName, personDetails
    
    # Load config
    admin_config = {
        "clinic_name": "Comprehensive Ocular Alignment Report",
        "doctor_name": "Dr. A. Narayana, MBBS, DOMS",
        "doctor_title": "Reviewing Ophthalmologist",
        "tech_name": "T. Kumar",
        "tech_title": "Examining Technician",
        "device_name": "EyeYantra v1.0",
        "contact_email": "reports@eyeyantra.health",
        "contact_phone": "+91 00000 00000"
    }
    if os.path.exists("admin_config.json"):
        try:
            with open("admin_config.json", "r", encoding="utf-8") as f:
                admin_config.update(json.load(f))
        except Exception as e:
            print(f"Error loading config: {e}")

    # Read registered patients from preliminary folder
    patients = []
    if os.path.exists("preliminary"):
        for f in os.listdir("preliminary"):
            if f.endswith(".jpg"):
                basename = f[:-4]
                parts = basename.split("_")
                # Expected format: Name_ID_DD_MM_YYYY_YYYY-MM-DD
                if len(parts) >= 6:
                    pname = parts[0]
                    pid = parts[1]
                    pdob = f"{parts[2]}/{parts[3]}/{parts[4]}"
                    pdate = parts[5]
                    raw_user = "_".join(parts[:5])
                    patients.append({
                        "name": pname,
                        "id": pid,
                        "dob": pdob,
                        "date": pdate,
                        "raw_username": raw_user
                    })
                elif len(parts) >= 2:
                    # Fallback
                    pname = parts[0]
                    pdate = parts[-1]
                    raw_user = "_".join(parts[:-1])
                    patients.append({
                        "name": pname,
                        "id": "N/A",
                        "dob": "N/A",
                        "date": pdate,
                        "raw_username": raw_user
                    })
    # Sort patients by date descending
    patients.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "admin.html",
        admin_config=admin_config,
        connected=connected_device,
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails,
        patients=patients[:15]  # Show up to last 15 patients
    )


@app.route("/set_active_patient", methods=["POST"])
def set_active_patient():
    global userName, personDetails
    
    pname = request.form.get("name")
    pid = request.form.get("id")
    pdob = request.form.get("dob")
    
    if not pname or not pid or not pdob:
        return jsonify({"status": "error", "message": "Invalid patient details."}), 400
        
    personDetails["userName"] = pname
    personDetails["id"] = pid
    personDetails["dob"] = pdob
    
    # Generate sanitized userName
    dob_sanitized = pdob.replace("/", "_")
    raw_user_name = f"{pname}_{pid}_{dob_sanitized}"
    userName = re.sub(r'[\\/*?:"<>|]', '_', raw_user_name)
    
    return jsonify({
        "status": "success", 
        "message": f"Successfully loaded session for {pname}!"
    })


@app.route("/edit_patient", methods=["POST"])
def edit_patient():
    global userName, personDetails
    
    old_raw = request.form.get("old_raw_username")  # e.g., akshaya_12345_18_01_2006
    new_name = request.form.get("name", "").strip()
    new_id = request.form.get("id", "").strip()
    new_dob = request.form.get("dob", "").strip()   # e.g., 18/01/2006
    
    if not old_raw or not new_name or not new_id or not new_dob:
        return jsonify({"status": "error", "message": "All fields are required."}), 400
        
    # Generate new raw username
    dob_sanitized = new_dob.replace("/", "_")
    new_raw_raw = f"{new_name}_{new_id}_{dob_sanitized}"
    new_raw = re.sub(r'[\\/*?:"<>|]', '_', new_raw_raw)
    
    if old_raw == new_raw:
        return jsonify({"status": "success", "message": "No changes made."})
        
    # Directories to scan and rename files/folders in
    folders = [
        "preliminary",
        "captured_images",
        "Preliminary_Results",
        "Hirschberg_Results",
        "HirschbergTestImages",
        "9GazeResults",
        "9GazeTestImages"
    ]
    
    rename_count = 0
    errors = []
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
            
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            
            # Case 1: Subdirectories containing the old username
            if os.path.isdir(item_path):
                if old_raw in item:
                    new_item_name = item.replace(old_raw, new_raw)
                    new_item_path = os.path.join(folder, new_item_name)
                    try:
                        os.rename(item_path, new_item_path)
                        rename_count += 1
                    except Exception as ex:
                        errors.append(f"Folder rename failed ({item}): {ex}")
            
            # Case 2: Files containing the old username
            elif os.path.isfile(item_path):
                if old_raw in item:
                    new_item_name = item.replace(old_raw, new_raw)
                    new_item_path = os.path.join(folder, new_item_name)
                    try:
                        os.rename(item_path, new_item_path)
                        rename_count += 1
                    except Exception as ex:
                        errors.append(f"File rename failed ({item}): {ex}")
                        
    # If the edited patient is the currently active patient, update the active session variables!
    if userName == old_raw:
        personDetails["userName"] = new_name
        personDetails["id"] = new_id
        personDetails["dob"] = new_dob
        userName = new_raw
        
    if errors:
        return jsonify({
            "status": "partial_success", 
            "message": f"Renamed {rename_count} items, but some errors occurred:\n" + "\n".join(errors)
        })
        
    return jsonify({
        "status": "success", 
        "message": f"Successfully updated patient records! Renamed {rename_count} items."
    })


@app.route("/save_admin_config", methods=["POST"])
def save_admin_config():
    admin_config = {
        "clinic_name": request.form.get("clinic_name"),
        "doctor_name": request.form.get("doctor_name"),
        "doctor_title": request.form.get("doctor_title"),
        "tech_name": request.form.get("tech_name"),
        "tech_title": request.form.get("tech_title"),
        "device_name": request.form.get("device_name"),
        "contact_email": request.form.get("contact_email"),
        "contact_phone": request.form.get("contact_phone")
    }
    # Validate
    for k, v in admin_config.items():
        if not v:
            return jsonify({"status": "error", "message": f"{k.replace('_', ' ').capitalize()} is required."}), 400
            
    try:
        with open("admin_config.json", "w", encoding="utf-8") as f:
            json.dump(admin_config, f, indent=2)
        return jsonify({"status": "success", "message": "Configuration saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/upload_preliminary", methods=["POST"])
def upload_preliminary():
    global userName
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded", "status": "error"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected", "status": "error"}), 400
    
    name = userName
    date = request.form.get("date")
    if not name:
        return jsonify({"message": "Name required", "status": "error"}), 400
    if not date:
        date = datetime.today().strftime('%Y-%m-%d')
        
    try:
        in_memory_file = file.read()
        nparr = np.frombuffer(in_memory_file, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"message": "Invalid image format", "status": "error"}), 400
            
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        filename = os.path.join(PRELIMINARY_FOLDER, f"{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(filename):
                os.remove(filename)
            return jsonify({"message": eye_status, "retry": True, "status": "error"})

        try:
            processed_filename = f"{name}_{date}.jpg"
            processed_path = os.path.join("Preliminary_Results", processed_filename)
            from results_processing import analyze_eyes
            analyze_eyes(frame.copy(), processed_path, processed_filename)
            print(f"✅ Proactively processed uploaded preliminary image for {name}")
        except Exception as pe:
            print(f"⚠️ Proactive preliminary processing failed: {pe}")

        return jsonify({"message": f"Image saved as {filename}", "status": "success"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {e}", "status": "error"}), 500


@app.route("/api/upload_hirschberg", methods=["POST"])
def upload_hirschberg():
    global userName
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded", "status": "error"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected", "status": "error"}), 400
    
    name = userName
    date = request.form.get("date")
    if not name or not date:
        return jsonify({"message": "Name and date required", "status": "error"}), 400
        
    try:
        in_memory_file = file.read()
        nparr = np.frombuffer(in_memory_file, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"message": "Invalid image format", "status": "error"}), 400
            
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        filename = os.path.join(HIRSCHBERG_RESULTS_FOLDER, f"hirschberg_{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(filename):
                os.remove(filename)
            return jsonify({"message": eye_status, "retry": True, "status": "error"})

        try:
            flipped_frame = cv2.flip(frame, 1)
            from hirschberg_analysis import analyze_hirschberg
            analyze_hirschberg(flipped_frame, "Hirschberg_Results", f"hirschberg_{name}_{date}.jpg")
            print(f"✅ Proactively processed uploaded Hirschberg image for {name}")
        except Exception as he:
            print(f"⚠️ Proactive Hirschberg processing failed: {he}")

        return jsonify({"message": f"Image saved as {filename}", "status": "success"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {e}", "status": "error"}), 500


@app.route("/api/upload_9gaze", methods=["POST"])
def upload_9gaze():
    global userName
    if 'file' not in request.files:
        return jsonify({"message": "No file uploaded", "status": "error"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No file selected", "status": "error"}), 400
    
    name = userName
    date = datetime.today().strftime('%Y-%m-%d')
    name = f"{name}_{date}"
    
    gaze_position = request.form.get("gaze")
    if not name or not gaze_position:
        return jsonify({"message": "Name and gaze required", "status": "error"}), 400
        
    gaze_map = {
        "upleft": "1",
        "up": "2",
        "upright": "3",
        "left": "4",
        "center": "5",
        "right": "6",
        "downleft": "7",
        "down": "8",
        "downright": "9"
    }
    if not str(gaze_position).isdigit():
        mapped_gaze = gaze_map.get(str(gaze_position).lower().strip())
        if mapped_gaze:
            gaze_position = mapped_gaze

    try:
        in_memory_file = file.read()
        nparr = np.frombuffer(in_memory_file, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({"message": "Invalid image format", "status": "error"}), 400

        temp_image_path = "temp_gaze.jpg"
        cv2.imwrite(temp_image_path, frame)

        eye_status = check_eye_status(temp_image_path)
        print(f"🔍 Eye status: {eye_status}")
        if "closed" in eye_status.lower() or "no face detected" in eye_status.lower():
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            return jsonify({"message": eye_status, "retry": True, "status": "error"})

        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

        person_folder = os.path.join(GAZE_TEST_FOLDER, name)
        if not os.path.exists(person_folder):
            os.makedirs(person_folder)

        image_filename = f"gaze_{gaze_position}.jpg"
        image_path = os.path.join(person_folder, image_filename)
        cv2.imwrite(image_path, frame)

        return jsonify({"message": f"✅ Image saved: {image_filename}", "status": "success"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {e}", "status": "error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
