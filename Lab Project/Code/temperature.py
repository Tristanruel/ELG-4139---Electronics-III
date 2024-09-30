import adafruit_dht
import board
import time
import RPi.GPIO as GPIO
import os
import glob

# Initialize 1-Wire for DS18B20 sensors
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Setup for DHT22
sensor = adafruit_dht.DHT22(board.D3)

# Setup for water sensor
water_pin = 2
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setup(water_pin, GPIO.IN)  # Set pin as an input

# Base directory for DS18B20 sensor details
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')  # DS18B20 sensors

# Sensor naming based on IDs
sensor_names = {
    '28-3c01f0965cb3': 'Ground Temperature 2',
    '28-3c01f0963fbc': 'Ground Temperature 1'
}

# Read raw temperature data from DS18B20
def read_temp_raw(device_file):
    with open(device_file, 'r') as file:
        valid_lines = file.readlines()
    return valid_lines

# Convert raw data to Celsius for DS18B20
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        # Check sensor ID and apply corrections
        if device_file.endswith('28-3c01f0963fbc/w1_slave'):  # Ground Temperature 1
            temp_c -= 3.0  # Subtract 3 degrees
        elif device_file.endswith('28-3c01f0965cb3/w1_slave'):  # Ground Temperature 2
            temp_c -= 5.0  # Subtract 5 degrees
        return temp_c

try:
    while True:
        # Read from DHT22
        try:
            temperature = sensor.temperature - 4.5
            humidity = sensor.humidity
            if humidity is not None and temperature is not None:
                print(f"Air Temperature: {temperature:.1f} C")
                print(f"Humidity: {humidity:.1f} %")
            else:
                print("Failed to retrieve data from humidity sensor")
        except RuntimeError as error:
            print(error.args[0])

        # Read from water sensor
        water_detected = GPIO.input(water_pin)
        print("Water: Yes" if water_detected else "Water: No")

        # Read from DS18B20 sensors
        for device_folder in device_folders:
            device_file = device_folder + '/w1_slave'
            ground_temp = read_temp(device_file)
            sensor_id = device_folder.split('/')[-1]
            sensor_name = sensor_names.get(sensor_id, 'Unknown Sensor')
            print(f"{sensor_name}: {ground_temp:.1f} °C")

        # Delay for a second before the next read
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped by User")
