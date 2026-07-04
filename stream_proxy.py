import flask
import threading
import requests
from flask import Response

app = flask.Flask(__name__)

# Global variables
stream_response = None  # Update this dynamically


@app.route("/video_feed")
def video_feed():
    """ Forward the MJPEG stream from stream_response. """
    global stream_response

    if stream_response is None:
        return "❌ No stream available", 404

    def generate():
        try:
            for chunk in stream_response.iter_content(chunk_size=1024):
                yield chunk  # Forward each chunk directly
        except Exception as e:
            print(f"❌ Streaming error: {e}")

    return Response(generate(), content_type="multipart/x-mixed-replace; boundary=--frame")


# Run the proxy in a separate thread
def start_proxy():
    threading.Thread(target=lambda: app.run(host="127.0.0.1", port=8080, debug=False, use_reloader=False)).start()


if __name__ == "__main__":
    start_proxy()
