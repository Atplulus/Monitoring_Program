from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
from random import random
from threading import Lock
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5173"}})  # Allow requests from Vite React frontend

thread = None
thread_lock = Lock()

def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")

def background_thread():
    print("Generating random sensor values")
    while True:
        dummy_sensor_value = round(random() * 100, 3)
        socketio.emit('sensorData', {'value': dummy_sensor_value, "date": get_current_datetime()})
        socketio.sleep(1)

@app.route('/')
def index():
    return "Data endpoint"

@socketio.on('connect')
def connect():
    global thread
    print('Client connected')

    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5001)