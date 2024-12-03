import cv2
import base64
import numpy as np
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
# CORS(app, resources={r"/*":{"origins":"http://localhost:3000"}})
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def capture_video():
    try :
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            _, buffer = cv2.imencode('.jpg',frame)
            frame_data = base64.b64encode(buffer).decode('utf-8')
            # print(len(frame_data))

            socketio.emit('video_response',frame_data)
            socketio.sleep(0.1)
    
    except Exception as e:
        print(f"error : {e}")
        socketio.emit('error', str(e))

    finally:
        cap.release()

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.start_background_task(capture_video)

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
        # cors_allowed_origins="http://localhost:3000"
    )