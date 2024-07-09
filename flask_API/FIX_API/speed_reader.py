import serial
import threading
import time
import json
import csv

class Readspeed:
    def __init__(self, port, baud_rate, callback, csv_filename, timeout=1):
        self.serial_port = serial.Serial(port, baud_rate)
        self.stop_event = threading.Event()
        self.callback = callback
        self.timeout = timeout  # Timeout in seconds
        self.csv_filename = csv_filename

        # Open the CSV file in write mode and write the header
        self.csv_file = open(self.csv_filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp", "Speed"])

    def read_speed(self):
        start_time = time.time()
        while not self.stop_event.is_set():
            if time.time() - start_time > self.timeout:
                print("Speed reading timed out. Stopping thread.")
                return
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
            except UnicodeDecodeError as e:
                print(f"Unicode decode error: {e}")
                continue

            if line:  # Check if line is not empty
                try:
                    # Parse the JSON data
                    data = json.loads(line)
                    # Extract the speed value and convert to float
                    speed = float(data['speed'])
                    timestamp = time.time()
                    self.callback(speed)
                    # Write the timestamp and speed to the CSV file
                    self.csv_writer.writerow([timestamp, speed])
                except (ValueError, KeyError, json.JSONDecodeError) as e:
                    print(f"Unable to process line: {line}. Error: {e}")
            else:
                print("No data received from the sensor. Returning from read_speed.")
                return  # Return from the method if no data is received

    def stop(self):
        self.stop_event.set()
        self.csv_file.close()  # Close the CSV file when stopping

# Example callback function
def my_callback(speed):
    print(f"Speed: {speed} km/h")

# Example usage
if __name__ == "__main__":
    reader = Readspeed("COM15", 115200, my_callback, "speed_data.csv")
    read_thread = threading.Thread(target=reader.read_speed)
    read_thread.start()

    # Run for some time and then stop
    time.sleep(10)
    reader.stop()
    read_thread.join()
