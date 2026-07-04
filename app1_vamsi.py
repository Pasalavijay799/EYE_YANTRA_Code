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
#from eye_detection import check_eye_status  # Import the eye detection function
from results_processing import show_results  # Import the function
from HirschbergTest_Processing import HirschbergShowResult  # Import Hirschberg processing function
from eye_detection import check_eye_status  # Import eye status function
from NineGazeProcessing import process_nine_gaze_images
from process_nine_gaze_images import create_combined_image
import overallreport
from crop_eyes_from_image import crop_eyes_from_image

app = Flask(__name__)
app.secret_key = "my_secret_key_here"

# BLE UUIDs for AMB82
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_RX = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Write
CHARACTERISTIC_UUID_TX = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Notify

REALTEK_DEVICE_NAME = "AMEBA_BLE_DEV"

client = None
connected_device = None
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

import time

latest_frame = None
latest_frame_lock = threading.Lock()
camera_connected = False

def stream_reader():
    global stream_ip, latest_frame, camera_connected
    current_ip = None

    # Try to pre-load the stream IP from file on startup
    try:
        with open("stream_ip.json", "r") as f:
            data = json.load(f)
            loaded_ip = data.get("stream_ip", None)
            if loaded_ip:
                stream_ip = loaded_ip
                print(f"🎬 Preloaded stream IP from json: {stream_ip}")
    except Exception:
        pass

    while True:
        if not stream_ip or stream_ip.lower() == "none":
            camera_connected = False
            time.sleep(1)
            continue

        current_ip = stream_ip
        stream_url = f"http://{current_ip}:80"
        print(f"🎥 Connecting to Ameba camera stream at {stream_url}...")

        try:
            response = requests.get(stream_url, stream=True, timeout=5)
            if response.status_code == 200:
                print(f"✅ Camera stream connected successfully to {current_ip}")
                camera_connected = True
                bytes_data = bytes()

                for chunk in response.iter_content(chunk_size=4096):
                    # Check if stream_ip was changed or cleared during streaming
                    if stream_ip != current_ip:
                        print("🔄 Stream IP changed, reconnecting...")
                        break

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
                            else:
                                bytes_data = bytes_data[a:]
                        else:
                            break
            else:
                print(f"⚠️ Stream returned status code: {response.status_code}")
                camera_connected = False
                time.sleep(2)
        except Exception as e:
            print(f"❌ Error in camera stream reader: {e}")
            camera_connected = False
            time.sleep(2)

# Start the background stream reader thread
threading.Thread(target=stream_reader, daemon=True).start()

placeholder_frame = None

def get_placeholder_frame():
    global placeholder_frame
    if placeholder_frame is None:
        # Create a black image (480x320)
        img = np.zeros((320, 480, 3), dtype=np.uint8)
        # Fill with a beautiful dark slate background to match the glassmorphism theme
        img[:] = (35, 16, 11) # BGR for dark slate #111023
        
        # Add text: "Connecting to" and "Headset Camera..."
        text1 = "Connecting to"
        text2 = "Headset Camera..."
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
    def generate():
        global latest_frame
        while True:
            frame_to_send = None
            is_placeholder = False
            with latest_frame_lock:
                if latest_frame is not None:
                    frame_to_send = latest_frame.copy()
                else:
                    frame_to_send = get_placeholder_frame()
                    is_placeholder = True

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

    return Response(generate(), content_type="multipart/x-mixed-replace; boundary=frame")


'''
def add_message(message):
    global stream_ip
    if not message.strip():
        return
    print(f"📥 Received from BLE: {message}")
    received_messages.put(message)

    # Capture stream IP
    if message.startswith("IP:"):
        stream_ip = message[3:].strip()'''

def add_message(message):
    global stream_ip, stream_response
    if not message.strip():
        return
    print(f"📥 Received from BLE: {message}")
    received_messages.put(f"📥 Received from BLE: {message}")
    # Capture stream IP
    if message.startswith("IP:"):
        stream_ip = message[3:].strip()
        save_stream_ip(stream_ip)
        print(f"🔍 Stream IP captured: {stream_ip}")
        received_messages.put(f"🔍 Stream IP captured: {stream_ip}")
        

@app.route("/get_stream_ip")
def get_stream_ip():
    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())
    return jsonify({
        "stream_ip": stream_ip,
        "connected_device": connected_device,
        "userName": userName,
        "messages": messages
    })


async def scan_devices():
    try:
        devices = await BleakScanner.discover()
        return [(device.name, device.address) for device in devices if device.name]
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
def global_notification_handler(sender, data):
    try:
        msg = data.decode("utf-8", errors="ignore")
        print(f"📥 [BLE Notify] {msg}")
        print("global notification handler")
        add_message(msg)
        # Optionally: received_messages.put(msg)
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
    global client, connected_device
 
    print(f"🔗 [BLE] Connecting to {address} in shared event loop...")
    client = BleakClient(address)
 
    try:
        await client.connect()
        connected_device = address
        print(f"✅ [BLE] Connected to {address}")
        received_messages.put(f"✅ [BLE] Connected to {address}")
 
        # Start notifications using a global or shared handler
        await client.start_notify(CHARACTERISTIC_UUID_TX, global_notification_handler)
        print("🔔 [BLE] Notifications enabled")
        received_messages.put("🔔 [BLE] Notifications enabled")
 
        while client.is_connected:
             await asyncio.sleep(0.5)
 
    except Exception as e:
        print(f"❌ [BLE] Connection error: {repr(e)}")
        received_messages.put(f"❌ [BLE] Connection error: {repr(e)}")
    finally:
        print(f"❌ [BLE] Connection closed for {address}")
        received_messages.put("❌ [BLE] Connection closed")
        connected_device = None

async def send_ble_message(message):
    if client and client.is_connected:
        try:
            await client.write_gatt_char(CHARACTERISTIC_UUID_RX, (message + "\n").encode())
            print(f"📤 Sent to BLE: {message}")
            received_messages.put(f"📤 Sent: {message}")
            #return redirect(url_for("index"))
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
                userName = f'{personDetails["userName"]}_{personDetails["id"]}_{personDetails["dob"]}'
                print("Login successful. Opening Bluetooth page...")
                return redirect(url_for("bluetooth"))
        
        elif "address" in request.form:
            address = request.form.get("address")
            name = request.form.get("name")
            print(f"🔗 [BLE] Received request to connect to {name} ({address})")
            asyncio.run_coroutine_threadsafe(connect_and_store_client(address), ble_loop)
            return redirect(url_for("bluetooth"))

        elif "ssid" in request.form and "password" in request.form and connected_device:
            ssid = request.form.get("ssid")
            password = request.form.get("password")
            wifi_credentials = f"{ssid},{password}"
            asyncio.run_coroutine_threadsafe(send_ble_message(wifi_credentials), ble_loop)
            return redirect(url_for("bluetooth"))

    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())

    if not userName:
       return render_template("index.html", devices=[], connected=connected_device, messages=messages, stream_ip=stream_ip, userName=userName, personDetails=personDetails)
    
    if connected_device:
        devices = []
    else:
        devices = asyncio.run(scan_devices())

    return render_template("index.html", devices=devices, connected=connected_device, messages=messages, stream_ip=stream_ip, userName=userName, personDetails=personDetails)

@app.route("/bluetooth")
def bluetooth():
    global connected_device, stream_ip, userName, personDetails
    
    if connected_device:
        devices = []
    else:
        devices = asyncio.run(scan_devices())

    messages = []
    while not received_messages.empty():
        messages.append(received_messages.get())

    return render_template(
        "index2.html",
        devices=devices,
        connected=connected_device,
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
    stream_ip = None  # Stores the received IP address
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
        json.dump({"stream_ip": ip}, f)

def load_stream_ip():
    """Load the IP address from the file if it exists."""
    global stream_ip
    try:
        with open(STREAM_IP_FILE, "r") as f:
            data = json.load(f)
            stream_ip = data.get("stream_ip", None)
    except (FileNotFoundError, json.JSONDecodeError):
        stream_ip = None  # Default to None if file not found or invalid

#load_stream_ip()
@app.route("/capture", methods=["POST"])
def capture():
    global userName  # Keep track of the user
    print(f"🔍 Debug: Capturing from cached stream frame")

    load_stream_ip()
    if not stream_ip or stream_ip.lower() == "none":
        return jsonify({"message": "No stream available.","status":"error"}), 400  

    name = userName
    date = request.form.get("date")

    if not name or not date:
        return jsonify({"message": "Name and date required.","status":"error"}), 400

    try:
        frame = None
        with latest_frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            return jsonify({"message": "Could not capture image from stream buffer yet. Please make sure the stream is open.","status":"error"}), 500

        # 📝 Overlay name & date on image
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 💾 Save image
        filename = os.path.join(UPLOAD_FOLDER, f"captured_{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
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
        frame = None
        with latest_frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            return jsonify({"message": "❌ Could not capture image from stream buffer yet. Please make sure the stream is open.","status":"error"}), 500

        # 📝 Overlay name & date
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 💾 Save image in the "preliminary" folder with new format `{name}_{date}.jpg`
        filename = os.path.join(PRELIMINARY_FOLDER, f"{name}_{date}.jpg")
        cv2.imwrite(filename, frame)

        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            os.remove(filename)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry
        
        #crop_eyes_from_image(filename)

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

        file_path = os.path.join(folder, filename)

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

        file_path = os.path.join(folder, filename)
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
    load_stream_ip()
    
    if not stream_ip or stream_ip.lower() == "none":
        return jsonify({"message": "❌ No stream available.","status":"error"}), 400

    return render_template(
        "hirschbergTest.html",
        stream_ip=stream_ip,
        userName=userName,
        personDetails=personDetails,
        connected=connected_device
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

    if not stream_ip or stream_ip.lower() == "none":
        return jsonify({"message": "No stream available.","status":"error"}), 400

    name = userName
    date = request.form.get("date")

    if not name or not date:
        return jsonify({"message": "Name and date required.","status":"error"}), 400

    # Step 1: Send LightOn command via BLE and wait for confirmation
    future = asyncio.run_coroutine_threadsafe(send_ble_command("LightOn", "LightOn", timeout=60), ble_loop)
    success = future.result()  # Optional timeout to avoid hanging
    print("success", success)

    if not success:
        return jsonify({"message": "Failed to turn on light.","status":"error"}), 500

    # Wait briefly for the LED light to be captured in the video stream frames
    time.sleep(0.3)

    try:
        # Step 2: Capture the last frame from the stream proxy buffer
        frame = None
        with latest_frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            return jsonify({"message": "Could not decode image.","status":"error"}), 500

        # Step 3: Overlay name & date on image
        text = f"{name} - {date}"
        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Step 4: Save image
        filename = os.path.join(HIRSCHBERG_RESULTS_FOLDER, f"hirschberg_{name}_{date}.jpg")
        cv2.imwrite(filename, frame)
        eye_status = check_eye_status(filename)
        print(f"🔍 Eye status: {eye_status}")
        if "error" in eye_status.lower() or "no face detected" in eye_status.lower():
            os.remove(filename)  # Remove temp file
            return jsonify({"message": eye_status, "retry": True,"status":"error"})  # Alert user to retry
        #crop_eyes_from_image(filename)
        print("after capturing frame in hirschberg test image")

    except Exception as e:
        return jsonify({"message": f"Error capturing image: {e}","status":"error"}), 500

    # Step 5: Send LightOff command via BLE and wait for confirmation
    # success = asyncio.run(send_ble_command("LightOff", "LightOff", timeout=60))
    # if not success:
    #     print("🔁 Retrying LightOff command...")
    #     success = asyncio.run(send_ble_command("LightOff", "LightOff", timeout=60))

    #testing
    try:
        future = asyncio.run_coroutine_threadsafe(send_ble_command("LightOff", "LightOff", timeout=60), ble_loop)
        success = future.result()
    except Exception as e:
        print(f"❌ LightOff command failed: {e}")
        success = False

    # Optional retry
    if not success:
        print("🔁 Retrying LightOff command...")
        try:
            future = asyncio.run_coroutine_threadsafe(send_ble_command("LightOff", "LightOff", timeout=60), ble_loop)
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

    if not stream_ip or stream_ip.lower() == "none":
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
        frame = None
        with latest_frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()

        if frame is None:
            return jsonify({"message": "Could not decode image.","status":"error"}), 500

        # Save the temporary image for checking eye status
        temp_image_path = "temp_gaze.jpg"
        cv2.imwrite(temp_image_path, frame)

        # Check if eyes are open
        eye_status = check_eye_status(temp_image_path)
        print(f"🔍 Eye status: {eye_status}")
        if "closed" in eye_status.lower() or "no face detected" in eye_status.lower():
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
    
    processed_folder = os.path.join(output_folder, f"{name}_Areal")

    if not os.path.exists(os.path.join(processed_folder, filename)):
        return "❌ File not found.", 404

    return send_from_directory(processed_folder, filename)


@app.route("/generate_overall_report", methods=["GET"])
def generate_overall_report():
    global personDetails
    try:
        pdf_path, pattern_result = overallreport.generate_pdf_report(personDetails=personDetails)
        return jsonify({"status": "success", "pattern": pattern_result})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@app.route("/download_overall_report", methods=["GET"])
def download_overall_report():
    pdf_path = "Overall_Report.pdf"
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    else:
        return "❌ Report not found.", 404


if __name__ == "__main__":
    app.run(debug=True)
