import serial
import threading
import time
import csv
from datetime import datetime
from flask_cors import CORS
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask app and SocketIO
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, origins=["http://localhost:5173"])

# Serial port configuration
rfid_serial_port = serial.Serial("COM13", 115200)

# Function to format tag ID with spaces
def format_tag_id(tag_id):
    return ' '.join(format(byte, '02X') for byte in tag_id)

# Function to read tags
def read_tag(stop_event):
    tag_names = {
        b'\xE2\x00\x20\x23\x12\x05\xEE\xAA\x00\x01\x00\x73': "TAG 1",
        b'\xE2\x00\x20\x23\x12\x05\xEE\xAA\x00\x01\x00\x76': "TAG 2",
        b'\xE2\x00\x20\x23\x12\x05\xEE\xAA\x00\x01\x00\x90': "TAG 3",
        b'\xE2\x00\x20\x23\x12\x05\xEE\xAA\x00\x01\x00\x87': "TAG 4",
        b'\xE2\x00\x20\x23\x12\x05\xEE\xAA\x00\x01\x00\x88': "TAG 5"
    }

    # Open CSV file and write header
    with open('rfid_data.csv', mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Timestamp', 'Tag Name', 'Tag ID'])

        while not stop_event.is_set():
            command = b'\x43\x4D\x02\x02\x00\x00\x00\x00'  # Correct command
            rfid_serial_port.write(command)
            data = rfid_serial_port.read(26)

            if data:
                for tag, name in tag_names.items():
                    if tag in data:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        formatted_tag = format_tag_id(tag)
                        print(name + " detected:", formatted_tag, "at", timestamp)
                        socketio.start_background_task(target=emit_tag_data, name=name, tag_id=formatted_tag, timestamp=timestamp)
                        # Write data to CSV
                        csv_writer.writerow([timestamp, name, formatted_tag])
                        csv_file.flush()  # Ensure data is written to the file
                        break
            else:
                print("No data received")

            time.sleep(0.001)

# Function to emit tag data to WebSocket clients
def emit_tag_data(name, tag_id, timestamp):
    print(f"Emitting data: {name}, {tag_id}, {timestamp}")
    socketio.emit('tag_data', {'timestamp': timestamp, 'name': name, 'tag_id': tag_id})

# Function to stop RFID reading
def stop_reading(stop_event):
    stop_event.set()
    print("Stopping RFID reading...")

# Event object to stop RFID reading
stop_event = threading.Event()

# Thread to continuously read tags
rfid_thread = threading.Thread(target=read_tag, args=(stop_event,))
rfid_thread.start()

@app.route('/')
def index():
    return "RFID Reader WebSocket Server"

if __name__ == '__main__':
    # Start Flask-SocketIO server
    socketio.run(app, host='localhost', port=5000)

try:
    while True:
        user_input = input("Type 'stop' to stop RFID reading: ")
        if user_input.lower() == 'stop':
            break
        time.sleep(0.01)
finally:
    # After finishing, call the function to stop RFID reading
    stop_reading(stop_event)
    # Wait for the thread to finish
    rfid_thread.join()

    # Command to stop RFID operation
    stop_command = b'\x43\x4D\x03\x02\x02\x00\x00\x00\x00'
    rfid_serial_port.write(stop_command)

    # Read response from the device
    response = rfid_serial_port.read(10)  # Response length 10 bytes
    if response == b'\x43\x4D\x03\x03\x03\x00\x00\x00\x00\x00':
        print("RFID reading successfully stopped.")
    else:
        print("Failed to stop RFID reading.")

    # Close serial port
    rfid_serial_port.close()
