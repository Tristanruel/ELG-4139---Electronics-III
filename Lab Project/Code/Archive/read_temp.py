import os
import glob
import time

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Base directory for the sensor details
base_dir = '/sys/bus/w1/devices/'
# Find device folders starting with 28- (your sensors' IDs)
device_folders = glob.glob(base_dir + '28*')

# Sensor naming based on IDs
sensor_names = {
    '28-3c01f0965cb3': 'Ground Temperature 2',
    '28-3c01f0963fbc': 'Ground Temperature 1'
}

# Read temperature data from the sensor
def read_temp_raw(device_file):
    with open(device_file, 'r') as file:
        valid_lines = file.readlines()
    return valid_lines

# Convert the raw temperature data into Celsius
def read_temp(device_file):
    lines = read_temp_raw(device_file)
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw(device_file)
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

# Main loop to read and print temperatures
try:
    while True:
        for device_folder in device_folders:
            device_file = device_folder + '/w1_slave'
            sensor_id = device_folder.split('/')[-1]
            sensor_name = sensor_names.get(sensor_id, 'Unknown Sensor')
            temp = read_temp(device_file)
            print(f'Temperature for {sensor_name}: {temp} °C')
        time.sleep(1)
except KeyboardInterrupt:
    print("\n Stopped by User")
