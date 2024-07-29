import serial
import threading
from flask_cors import CORS
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import csv

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, origins=["http://localhost:5173"])

# Declare the serial port
ser = serial.Serial('COM15', 9600)

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

# Open the CSV file in write mode and write the header
csv_filename = 'speed_data.csv'
csv_file = open(csv_filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Timestamp", "Speed"])

# Example usage:
def example_callback(speed):
    timestamp = get_current_datetime()
    print(f"Speed: {speed}, Timestamp: {timestamp}")
    socketio.emit('speed_update', {'speed': speed, 'timestamp': timestamp})
    # Write the timestamp and speed to the CSV file
    csv_writer.writerow([timestamp, speed])
    csv_file.flush()  # Ensure data is written to the file

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
    csv_file.close()  # Close the CSV file

if __name__ == '__main__':
    socketio.run(app, host='localhost', port=5002)
