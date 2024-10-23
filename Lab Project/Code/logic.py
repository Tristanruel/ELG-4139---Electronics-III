import threading
import time
import adafruit_dht
import board
import RPi.GPIO as GPIO
import os
import glob
import requests
import sqlite3
from datetime import datetime, timedelta
import gpsd
import pytz
import ntplib
import pvlib
from pvlib.location import Location
from pvlib.solarposition import get_solarposition
import pandas as pd

# Constants
FLOW_RATE = 16  # L/min
GARDEN_AREA = 10  # square meters, assumed garden area
BASELINE_WATER_PER_SQ_METER = 5  # L/m²/day
W_BASE = BASELINE_WATER_PER_SQ_METER * GARDEN_AREA  # total baseline water need per day

# Initialize a lock for thread-safe access to sensor data
sensor_data_lock = threading.Lock()
weather_data_lock = threading.Lock()

sensor_data = {
    'air_temperature': None,  # in °C
    'air_humidity': None,     # in %
    'ground_temp_1': None,    # °C, at 0.5 in depth
    'ground_temp_2': None,    # °C, at 5 in depth
    'water_sensor': 'No',     # 'Yes' or 'No'
}

# Initialize weather_data to store current weather and precipitation data
weather_data = {
    'current_weather': None,        # Dictionary containing current weather data
    'past_precipitation': 0.0,      # Total past precipitation in mm
    'forecasted_precipitation': 0.0, # Total forecasted precipitation in mm
}

def update_weather_data(current, past_precip, forecast):
    """
    Update the shared weather_data dictionary with new data.
    """
    with weather_data_lock:
        weather_data['current_weather'] = current
        weather_data['past_precipitation'] = past_precip
        weather_data['forecasted_precipitation'] = forecast

def calculate_adjusted_water_need():
    with sensor_data_lock, weather_data_lock:
        current_sensor_data = sensor_data.copy()
        current_weather = weather_data['current_weather']
        P_past = weather_data['past_precipitation']
        P_forecast = weather_data['forecasted_precipitation']

    if not current_weather:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No current weather data available.")
        return

    # use sensor data if available, else use current weather data
    T_current = current_sensor_data['air_temperature'] if current_sensor_data['air_temperature'] is not None else current_weather.get('temp_c', 20)  # def to 20°C if not available
    H_current = current_sensor_data['air_humidity'] if current_sensor_data['air_humidity'] is not None else current_weather.get('humidity', 50)  # def to 50% if not available

    # wind speed in kph from current weather data
    Wind_speed_kph = current_weather.get('wind_kph', 2)
    Wind_speed_mps = Wind_speed_kph / 3.6  # convert to m/s

    Cloud_cover = current_weather.get('cloud', 50)  # in %
    UV_index = current_weather.get('uv', 5)

    # adjustment factors
    F_temp = 1 + 0.02 * (T_current - 20)
    F_hum = 1 - 0.02 * ((H_current - 50) / 5)
    Wind_speed_base = 2  # m/s
    F_wind = 1 + 0.01 * (Wind_speed_mps - Wind_speed_base)

    # solar radiation factor (using cloud cover)
    F_solar = 1 + 0.05 * (1 - Cloud_cover / 100)
    F_env = F_temp * F_hum * F_wind * F_solar
    W_adj = W_BASE * F_env

    # precipitation adjustments
    # tot precipitation to subtract (convert mm to L)
    P_total = (P_past + P_forecast) * GARDEN_AREA  # mm * m² = L

    # adjusted water need after precipitation
    W_final = W_adj - P_total
    W_final = max(W_final, 0)  # ensure non-negative water need

    # runtime
    runtime_minutes = W_final / FLOW_RATE  # Flow rate in L/min
    runtime_seconds = runtime_minutes * 60 

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print(f"Sprinkler needs to run for {runtime_seconds:.2f} seconds. This equals {W_final:.2f}L of water for a garden of {GARDEN_AREA:.2f} square meters.")
    print(f"Total water applied: {P_total:.2f} L.\n")

def calculate_water_need_wrapper():
    """
    Wrapper function to calculate adjusted water need.
    Can include additional error handling if necessary.
    """
    try:
        calculate_adjusted_water_need()
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error in calculating water need: {e}")

def schedule_tasks():
    """
    Schedule tasks to run at specified intervals:
    - solar_position_function every 60 seconds
    - weathersql_function and weather_terminal_function 20 seconds after solar_position_function
    - calculate_adjusted_water_need 35 seconds after solar_position_function
    """
    while True:
        now = datetime.now()

        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        time_to_wait = (next_minute - now).total_seconds()

        time.sleep(time_to_wait)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled tasks.")

        solar_thread = threading.Thread(target=solar_position_function)
        solar_thread.start()

        threading.Timer(20, run_weathersql_and_terminal).start()

        threading.Timer(35, calculate_water_need_wrapper).start()

def run_weathersql_and_terminal():
    """
    Function to run weathersql_function and weather_terminal_function concurrently.
    After fetching weather data, update the shared weather_data dictionary.
    """
    def weathersql_thread_func():
        # Fetch weather data (simulate fetching current and forecasted precipitation)
        # Replace this with actual data fetching logic
        current_weather = {
            'temp_c': 25.0,
            'humidity': 60,
            'wind_kph': 10,
            'cloud': 40,
            'uv': 7,
            # Add other necessary fields as needed
        }
        # Simulate past and forecasted precipitation
        past_precipitation = 5.0  # mm
        forecasted_precipitation = 10.0  # mm

    
        update_weather_data(current_weather, past_precipitation, forecasted_precipitation)

    def weather_terminal_thread_func():
        # placeholder
        pass  

    weathersql = threading.Thread(target=weathersql_thread_func)
    weather_terminal = threading.Thread(target=weather_terminal_thread_func)

    weathersql.start()
    weather_terminal.start()

    weathersql.join()
    weather_terminal.join()

# ==========================
# End of Logic.py
# ==========================

def temperature_function():
    # Initialize 1-Wire for DS18B20 sensors
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    # Setup for DHT22
    sensor = adafruit_dht.DHT22(board.D3)

    # Setup for water sensor
    water_pin = 2
    GPIO.setmode(GPIO.BCM)  
    GPIO.setup(water_pin, GPIO.IN)  

    base_dir = '/sys/bus/w1/devices/'
    device_folders = glob.glob(base_dir + '28*')  

    # Sensor naming
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
        return None

    try:
        while True:
            # Read from DHT22
            try:
                temperature = sensor.temperature - 4.5 if sensor.temperature is not None else None
                humidity = sensor.humidity
                with sensor_data_lock:
                    sensor_data['air_temperature'] = temperature
                    sensor_data['air_humidity'] = humidity

                if humidity is not None and temperature is not None:
                    print(f"Air Temperature: {temperature:.1f} C")
                    print(f"Humidity: {humidity:.1f} %")
                else:
                    print("Failed to retrieve data from humidity sensor")
            except RuntimeError as error:
                print(error.args[0])

            # Read from water sensor
            water_detected = GPIO.input(water_pin)
            water_status = "Yes" if water_detected else "No"
            with sensor_data_lock:
                sensor_data['water_sensor'] = water_status
            print(f"Water: {water_status}")

            # Read from DS18B20 sensors
            for device_folder in device_folders:
                device_file = device_folder + '/w1_slave'
                ground_temp = read_temp(device_file)
                sensor_id = device_folder.split('/')[-1]
                sensor_name = sensor_names.get(sensor_id, 'Unknown Sensor')
                with sensor_data_lock:
                    if sensor_name == 'Ground Temperature 1':
                        sensor_data['ground_temp_1'] = ground_temp
                    elif sensor_name == 'Ground Temperature 2':
                        sensor_data['ground_temp_2'] = ground_temp
                print(f"{sensor_name}: {ground_temp:.1f} °C")

            # Delay for a second before the next read
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nTemperature monitoring stopped by User")
        GPIO.cleanup()

def relay_function():

    relay_pins = {1: 6, 2: 13, 3: 19, 4: 26}
    GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme
    GPIO.setup(list(relay_pins.values()), GPIO.OUT, initial=GPIO.HIGH)  

    def relay_command(command):
        """
        Accepts a command string to control relays, e.g., '1 ON', '2 OFF'.
        Handles active-low relays where 'ON' means setting GPIO to LOW.
        """
        try:
            relay_number, state = command.split()
            relay_number = int(relay_number)
            if relay_number in relay_pins:
                if state.upper() == 'OFF':
                    GPIO.output(relay_pins[relay_number], GPIO.HIGH)  
                    print(f"Relay {relay_number} turned OFF")
                elif state.upper() == 'ON':
                    GPIO.output(relay_pins[relay_number], GPIO.LOW) 
                    print(f"Relay {relay_number} turned ON")
                else:
                    print("Invalid state. Use 'ON' or 'OFF'.")
            else:
                print("Invalid relay number.")
        except ValueError:
            print("Command format error. Use '<relay number> <ON/OFF>'.")

    def cleanup():
        """
        Clean up GPIO assignments
        """
        GPIO.cleanup()

    try:
        while True:
            command = input("Enter relay command (e.g., '1 ON'): ")
            relay_command(command)
    except KeyboardInterrupt:
        cleanup()
        print("Relay control program exited cleanly")

def solar_position_function():
    def print_green(text):
        print(f"\033[92m{text}\033[0m")

    def print_red(text):
        print(f"\033[91m{text}\033[0m")

    try:
        gpsd.connect()
        print_green("GPSD connected successfully.")
    except Exception as e:
        print_red("Failed to connect to GPSD.")
        print_red(str(e))

    def get_ntp_time(ntp_server='time.google.com'):
        client = ntplib.NTPClient()
        try:
            response = client.request(ntp_server, version=3)
            ntp_time = datetime.utcfromtimestamp(response.tx_time)
            return ntp_time.replace(tzinfo=pytz.UTC)
        except Exception as e:
            print_red(f"Failed to get NTP time: {e}")
            return datetime.now(pytz.UTC)

    # Set backup coordinates and timezone
    default_latitude, default_longitude = 45.365977, -75.602712
    default_tz = 'America/New_York'  # Eastern Daylight Time (EDT) or Eastern Standard Time (EST) handled by pytz

    try:
        packet = gpsd.get_current()
        if packet.mode < 2:
            raise ValueError("GPS fix not available")
        latitude = packet.lat
        longitude = packet.lon
        gps_time = datetime.now(pytz.timezone(default_tz)).replace(microsecond=0)
        current_time = gps_time
        print_green("GPS data used for calculations.")
    except Exception as e:
        print_red(str(e))
        print_red("Using backup coordinates and NTP time...")
        latitude, longitude = default_latitude, default_longitude
        current_time = get_ntp_time()
        current_time = current_time.astimezone(pytz.timezone(default_tz))  # Ensure timezone is consistent

    print_green(f"Current local date and time: {current_time}")
    print_green(f"Current GPS coordinates: Latitude {latitude}, Longitude {longitude}")

    site = Location(latitude, longitude, tz=default_tz)
    start_time = current_time
    end_time = start_time + timedelta(days=1)

    times_range = pd.date_range(start=start_time, end=end_time, freq='1s', tz=site.tz)
    solar_pos = get_solarposition(times_range, latitude, longitude)

    # Filter for elevations between 10 and 11 degrees
    sun_between_10_and_11 = solar_pos[(solar_pos['elevation'] >= 10) & (solar_pos['elevation'] < 11)]

    if not sun_between_10_and_11.empty:
        # Calculate time until the sun reaches exactly 10 degrees
        first_time_at_10 = sun_between_10_and_11.iloc[0].name
        last_time_at_10 = sun_between_10_and_11.iloc[-1].name
        time_until_sun_at_10 = first_time_at_10 - current_time
        seconds_until_sun_at_10 = int(time_until_sun_at_10.total_seconds())
        hours = seconds_until_sun_at_10 // 3600
        remaining_seconds = seconds_until_sun_at_10 % 3600
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        future_time = current_time + timedelta(seconds=seconds_until_sun_at_10)

        print_green(f"Time until the sun is at 10 degrees: {hours:02d}h {minutes:02d}min {seconds:02d}s or at {future_time.strftime('%Y-%m-%d %H:%M:%S')} \n")

        # Write to countdown.txt
        with open("countdown.txt", "w") as file:
            file.write(f"{seconds_until_sun_at_10}")
        
        with open('coords.txt', 'w') as file:
            file.write(f"{latitude}, {longitude}")

        # Writing the first and last entries to a file
        with open("10degsun.txt", "w") as file:
            file.write(f"First time at 10-11 degrees: {first_time_at_10}\n")
            file.write(f"Last time at 10-11 degrees: {last_time_at_10}\n")
    else:
        print_red("There are no times within the next 24 hours when the sun is between 10 and 11 degrees elevation.")

    print(sun_between_10_and_11)

def weathersql_function():
    with open('coords.txt', 'r') as file:
        coords = file.read().strip()
    api_key = "216de71353404ef899e162434242709"
    query = coords
    url = "http://api.weatherapi.com/v1/forecast.json"

    params = {
        'key': api_key,
        'q': query,
        'days': 3  # fetch forecast for 3 days
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Extract current weather data
        current_weather = data['current']

        # Extract required fields
        current_weather_data = {
            'temp_c': current_weather['temp_c'],
            'humidity': current_weather['humidity'],
            'wind_kph': current_weather['wind_kph'],
            'cloud': current_weather['cloud'],
            'uv': current_weather['uv'],
            # Add other necessary fields if needed
        }

        # Initialize past and forecasted precipitation
        past_precipitation = 0.0
        forecasted_precipitation = 0.0

        current_date = datetime.now().date()

        # Sum up past and forecasted precipitation
        for day in data['forecast']['forecastday']:
            date_str = day['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            total_precip_mm = day['day']['totalprecip_mm']

            if date_obj < current_date:
                # Past date (if any)
                past_precipitation += total_precip_mm
            elif date_obj == current_date:
                # Today's date
                past_precipitation += total_precip_mm
            else:
                # Future dates
                forecasted_precipitation += total_precip_mm

        # Update the shared weather_data dictionary
        update_weather_data(current_weather_data, past_precipitation, forecasted_precipitation)
    else:
        print(f"Failed to retrieve weather data. HTTP status code: {response.status_code}")

def weather_terminal_function():
    with open('coords.txt', 'r') as file:
        coords = file.read().strip()
    url = "http://api.weatherapi.com/v1/forecast.json"
    apiKey = "216de71353404ef899e162434242709"
    query = coords

    params = {
        'key': apiKey,
        'q': query,
        'days': 3  
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        json_data = response.json()

        # Extract location information
        location = f"{json_data['location']['region']}, {json_data['location']['name']}, {json_data['location']['country']}"
        localTime = json_data['location']['localtime']

        # Extract current weather data
        weatherCondition = json_data['current']['condition']['text']
        tempC = json_data['current']['temp_c']
        windKph = json_data['current']['wind_kph']
        windDegree = json_data['current']['wind_degree']
        windDir = json_data['current']['wind_dir']
        pressureMb = json_data['current']['pressure_mb']
        pressureIn = json_data['current']['pressure_in']
        precipMm = json_data['current']['precip_mm']
        humidity = json_data['current']['humidity']
        cloud = json_data['current']['cloud']
        feelsLikeC = json_data['current']['feelslike_c']
        windChillC = json_data['current'].get('windchill_c', None)
        heatIndexC = json_data['current'].get('heatindex_c', None)
        dewPointC = json_data['current']['dewpoint_c']
        visKm = json_data['current']['vis_km']
        uv = json_data['current']['uv']
        gustKph = json_data['current']['gust_kph']

        print(f'Current weather in {location} on {localTime}')
        print(f'{weatherCondition}')
        print(f"Temperature: {tempC}°C")
        print(f"Wind Speed: {windKph} kph")
        print(f"Wind Degree: {windDegree}")
        print(f"Wind Direction: {windDir}")
        print(f"Pressure: {pressureMb} mb / {pressureIn} in")
        print(f"Precipitation: {precipMm} mm")
        print(f"Humidity: {humidity}%")
        print(f"Cloud Cover: {cloud}%")
        print(f"Feels Like: {feelsLikeC}°C")
        if windChillC is not None:
            print(f"Wind Chill: {windChillC}°C")
        if heatIndexC is not None:
            print(f"Heat Index: {heatIndexC}°C")
        print(f"Dew Point: {dewPointC}°C")
        print(f"Visibility: {visKm} km")
        print(f"UV Index: {uv}")
        print(f"Gust Speed: {gustKph} kph")

        # Extract and print forecast data for the next 3 days
        forecast_days = json_data['forecast']['forecastday']
        for day in forecast_days:
            date = day['date']
            date_epoch = day['date_epoch']
            day_data = day['day']
            astro = day['astro']

            maxtemp_c = day_data['maxtemp_c']
            maxtemp_f = day_data['maxtemp_f']
            mintemp_c = day_data['mintemp_c']
            mintemp_f = day_data['mintemp_f']
            avgtemp_c = day_data['avgtemp_c']
            avgtemp_f = day_data['avgtemp_f']
            maxwind_mph = day_data['maxwind_mph']
            maxwind_kph = day_data['maxwind_kph']
            totalprecip_mm = day_data['totalprecip_mm']
            totalprecip_in = day_data['totalprecip_in']
            totalsnow_cm = day_data['totalsnow_cm']
            avgvis_km = day_data['avgvis_km']
            avgvis_miles = day_data['avgvis_miles']
            avghumidity = day_data['avghumidity']
            daily_will_it_rain = day_data['daily_will_it_rain']
            daily_chance_of_rain = day_data['daily_chance_of_rain']
            daily_will_it_snow = day_data['daily_will_it_snow']
            daily_chance_of_snow = day_data['daily_chance_of_snow']
            condition_text = day_data['condition']['text']
            condition_icon = day_data['condition']['icon']
            condition_code = day_data['condition']['code']
            uv_index = day_data['uv']
            air_quality = day_data.get('air_quality', {})

            # Astro data
            sunrise = astro['sunrise']
            sunset = astro['sunset']
            moonrise = astro['moonrise']
            moonset = astro['moonset']
            moon_phase = astro['moon_phase']
            moon_illumination = astro['moon_illumination']
            is_moon_up = astro['is_moon_up']
            is_sun_up = astro['is_sun_up']

            print(f"\nForecast for {date}:")
            print(f"Date Epoch: {date_epoch}")
            print(f"Condition: {condition_text}")
            print(f"Condition Code: {condition_code}")
            print(f"Max Temp: {maxtemp_c}°C / {maxtemp_f}°F")
            print(f"Min Temp: {mintemp_c}°C / {mintemp_f}°F")
            print(f"Avg Temp: {avgtemp_c}°C / {avgtemp_f}°F")
            print(f"Max Wind Speed: {maxwind_kph} kph / {maxwind_mph} mph")
            print(f"Total Precipitation: {totalprecip_mm} mm / {totalprecip_in} in")
            print(f"Total Snowfall: {totalsnow_cm} cm")
            print(f"Avg Visibility: {avgvis_km} km / {avgvis_miles} miles")
            print(f"Avg Humidity: {avghumidity}%")
            print(f"Will it rain?: {'Yes' if daily_will_it_rain else 'No'}")
            print(f"Chance of rain: {daily_chance_of_rain}%")
            print(f"Will it snow?: {'Yes' if daily_will_it_snow else 'No'}")
            print(f"Chance of snow: {daily_chance_of_snow}%")
            print(f"UV Index: {uv_index}")

            # Air Quality
            if air_quality:
                print("Air Quality:")
                for pollutant, value in air_quality.items():
                    print(f"  {pollutant}: {value}")

            # Astro data
            print("Astro Data:")
            print(f"  Sunrise: {sunrise}")
            print(f"  Sunset: {sunset}")
            print(f"  Moonrise: {moonrise}")
            print(f"  Moonset: {moonset}")
            print(f"  Moon Phase: {moon_phase}")
            print(f"  Moon Illumination: {moon_illumination}%")

    else:
        print(f"Failed to retrieve weather data. HTTP status code: {response.status_code}")

def calculate_water_need_wrapper():
    try:
        calculate_adjusted_water_need()
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error in calculating water need: {e}")

def run_weathersql_and_terminal():
    # run weathersql_function and weather_terminal_function
    weathersql_thread = threading.Thread(target=weathersql_function)
    weather_terminal_thread = threading.Thread(target=weather_terminal_function)

    weathersql_thread.start()
    weather_terminal_thread.start()

    weathersql_thread.join()
    weather_terminal_thread.join()

def schedule_tasks():
    """
    Schedule tasks to run at specified intervals:
    - solar_position_function every 60 seconds
    - weathersql_function and weather_terminal_function 20 seconds after solar_position_function
    - calculate_adjusted_water_need 35 seconds after solar_position_function
    """
    while True:
        now = datetime.now()

        # Calculate time until the next full minute
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        time_to_wait = (next_minute - now).total_seconds()

        # Sleep until the next full minute
        time.sleep(time_to_wait)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled tasks.")

        # Run solar_position_function
        solar_thread = threading.Thread(target=solar_position_function)
        solar_thread.start()

        # Schedule weathersql and weather_terminal to run 20 seconds later
        threading.Timer(20, run_weathersql_and_terminal).start()

        # Schedule calculate_adjusted_water_need to run 35 seconds after solar_position_function
        threading.Timer(35, calculate_water_need_wrapper).start()

        # Total cycle time is 60 seconds; no need to wait here as the loop handles the scheduling

def calculate_and_run_logic():
    calculate_adjusted_water_need()

if __name__ == "__main__":
    # Initialize GPIO settings
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme

    # Start temperature_function in a separate thread
    temp_thread = threading.Thread(target=temperature_function)
    temp_thread.daemon = True
    temp_thread.start()

    # Start relay_function in a separate thread
    relay_thread = threading.Thread(target=relay_function)
    relay_thread.daemon = True
    relay_thread.start()

    # Run schedule_tasks in the main thread
    try:
        schedule_tasks()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        GPIO.cleanup()

