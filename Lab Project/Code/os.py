import threading
import time
import os

def run_temperature():
    while True:
        os.system("python3 temperature.py")
        time.sleep(1)  # runs temperature.py every second

def run_solar_position():
    while True:
        os.system("python3 solar_position.py")
        time.sleep(60)  # runs solar_position.py once every minute

def main():
    # Creating threads for both functions
    temperature_thread = threading.Thread(target=run_temperature)
    solar_position_thread = threading.Thread(target=run_solar_position)

    # Starting the threads
    temperature_thread.start()
    solar_position_thread.start()

    # Join threads to the main thread
    temperature_thread.join()
    solar_position_thread.join()

if __name__ == "__main__":
    main()
