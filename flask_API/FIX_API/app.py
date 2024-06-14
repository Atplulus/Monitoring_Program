import serial
import threading
from flask_cors import CORS
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, origins=["http://localhost:5173"])
# Declare the serial port
ser = serial.Serial('/dev/ttyACM0', 9600)

stop_event = threading.Event()
callback = None

def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")

def read_speed():
    while not stop_event.is_set():
        line = ser.readline().decode('utf-8').strip()
        if line:
            try:
                speed = float(line)
                callback(speed)
            except ValueError:
                print(f"Unable to convert line to float: {line}")
        else:
            print("No data received from the sensor. Returning from read_speed.")

def stop():
    stop_event.set()

# Example usage:
def example_callback(speed):
    timestamp = get_current_datetime()
    print(f"Speed: {speed}, Timestamp: {timestamp}")
    socketio.emit('speed_update', {'speed': speed, 'timestamp': timestamp})

callback = example_callback

# Create and start the serial reading thread
thread = threading.Thread(target=read_speed)
thread.start()

# WebSocket route
@app.route('/')
def index():
    return "Speed Reader WebSocket Server"

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Stop the serial reading thread when the app stops
@socketio.on('stop')
def handle_stop():
    stop()
    thread.join()

if __name__ == '__main__':
    socketio.run(app,host='localhost', port=5002)
