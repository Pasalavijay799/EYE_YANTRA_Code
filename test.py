import cv2
import threading
from flask import Flask, Response

app = Flask(__name__)

# Set your stream URL
stream_url = "http://10.26.94.196/"
frame = None

# Capture the frame in a separate thread
def capture_stream():
    global frame
    cap = cv2.VideoCapture(stream_url)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame from stream.")
            break

    cap.release()


# Generate MJPEG frames for the Flask route
def generate_frames():
    global frame
    while True:
        if frame is None:
            continue
        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")


@app.route("/")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    threading.Thread(target=capture_stream).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
