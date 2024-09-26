import adafruit_dht
import board
import time
import RPi.GPIO as GPIO

# Setup for DHT22
sensor = adafruit_dht.DHT22(board.D3)

# Setup for water sensor
water_pin = 2
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setup(water_pin, GPIO.IN)  # Set pin as an input

while True:
    try:
        # Read from DHT22
        temperature = sensor.temperature
        humidity = sensor.humidity

        # Read from water sensor
        water_detected = GPIO.input(water_pin)

        # Print temperature and humidity
        if humidity is not None and temperature is not None:
            print(f"Air Temperature: {temperature:.1f} C")
            print(f"Humidity: {humidity:.1f} %")
        else:
            print("Failed to retrieve data from humidity sensor")

        # Print water detection status
        if water_detected:
            print("Water: Yes")
        else:
            print("Water: No")

    except RuntimeError as error:
        print(error.args[0])

    # Delay for a second before the next read
    time.sleep(1)
