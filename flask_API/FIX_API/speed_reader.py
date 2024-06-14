# speed_app.py

from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import serial
import threading
import sys
from datetime import datetime

# Initialize Flask application
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
CORS(app, origins=["http://localhost:5173"])

# Configure serial port
serial_port_path = '/dev/ttyACM0'  # Adjust this as needed
baud_rate = 9600

class SensorReader:
    def __init__(self, port, baud_rate, callback):
        """
        Initialize sensor reading via serial port.
        
        port: Path to the serial port.
        baud_rate: Baud rate for serial communication.
        callback: Callback function to send data to the websocket.
        """
        self.serial_port = serial.Serial(port, baud_rate)
        self.callback = callback
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.read_speed)
        
    def read_speed(self):
        """
        Continuously read speed from the sensor.
        If data is received, call the callback with the data.
        """
        while not self.stop_event.is_set():
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                if line:
                    try:
                        speed = float(line)
                        self.callback(speed)
                    except ValueError:
                        print(f"Cannot convert line to float: {line}")
                else:
                    print("No data received from sensor.")
            except serial.SerialException as e:
                print(f"Serial exception: {e}")
                self.stop_event.set()
            except Exception as e:
                print(f"Unexpected exception: {e}")
                self.stop_event.set()

    def start(self):
        """
        Start the thread to read data from the sensor.
        """
        self.thread.start()

    def stop(self):
        """
        Stop reading data from the sensor and close the serial connection.
        """
        self.stop_event.set()
        self.thread.join()
        self.serial_port.close()

def send_speed_data(speed):
    """
    Send speed data to the websocket.
    
    :param speed: Speed data to be sent.
    """
    timestamp = datetime.now().isoformat()
    socketio.emit('sensor1_data', {'data': speed, 'timestamp': timestamp})

# Initialize sensor reading
sensor_reader = SensorReader(serial_port_path, baud_rate, send_speed_data)

@app.route('/sensor1')
def sensor1_data():
    """
    Endpoint to check the status of sensor reading.
    
    :return: JSON with the status of sensor reading.
    """
    return jsonify({'status': 'Sensor reading running'}), 200

if __name__ == '__main__':
    """
    Entry point of the application. Start sensor reading and run the Flask application with SocketIO.
    """
    sensor_reader.start()
    socketio.run(app, port=5002)
