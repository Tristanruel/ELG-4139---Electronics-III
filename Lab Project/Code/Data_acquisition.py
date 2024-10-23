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
        print("\nTemperature monitoring stopped by User")

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
                    print("Invalid command")
            else:
                print("Invalid relay number")
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
        response = client.request(ntp_server, version=3)
        ntp_time = datetime.utcfromtimestamp(response.tx_time)
        return ntp_time.replace(tzinfo=pytz.UTC)

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
    def fetch_weather_data(api_key, query, days=3):
        base_url = "http://api.weatherapi.com/v1"
        forecast_url = f"{base_url}/forecast.json"
        history_url = f"{base_url}/history.json"

        # Connect to SQLite Database
        db_connection = sqlite3.connect('weather_data.db')
        cursor = db_connection.cursor()

        # Create tables if not exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS weather_data (
                            date TEXT,
                            location TEXT,
                            condition TEXT,
                            condition_code INTEGER,
                            max_temp_c REAL,
                            min_temp_c REAL,
                            avg_temp_c REAL,
                            max_wind_kph REAL,
                            total_precip_mm REAL,
                            total_snow_cm REAL,
                            avg_visibility_km REAL,
                            avg_humidity INTEGER,
                            will_it_rain TEXT,
                            chance_of_rain INTEGER,
                            will_it_snow TEXT,
                            chance_of_snow INTEGER,
                            uv_index REAL,
                            sunrise TEXT,
                            sunset TEXT,
                            moonrise TEXT,
                            moonset TEXT,
                            moon_phase TEXT,
                            moon_illumination INTEGER,
                            is_moon_up TEXT,
                            is_sun_up TEXT,
                            recorded_time TEXT,
                            temp_c REAL,
                            wind_kph REAL,
                            wind_degree INTEGER,
                            wind_dir TEXT,
                            pressure_mb REAL,
                            pressure_in REAL,
                            precip_mm REAL,
                            humidity INTEGER,
                            cloud INTEGER,
                            feels_like_c REAL,
                            wind_chill_c REAL,
                            heat_index_c REAL,
                            dew_point_c REAL,
                            visibility_km REAL,
                            gust_kph REAL
                        )''')

        # Fetching forecast and current weather
        response = requests.get(f"{forecast_url}?key={api_key}&q={query}&days={days}")
        if response.status_code == 200:
            data = response.json()
            current_weather = data['current']
            save_weather_data(cursor, datetime.now().strftime('%Y-%m-%d %H:%M'), query, current_weather, 'current')

            for day in data['forecast']['forecastday']:
                save_weather_data(cursor, day['date'], query, day['day'], 'forecast')
                save_weather_data(cursor, day['date'], query, day['astro'], 'astro')

        # Historical weather for the last 3 days
        for i in range(1, 4):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            response = requests.get(f"{history_url}?key={api_key}&q={query}&dt={date}")
            if response.status_code == 200:
                data = response.json()
                historical_weather = data['forecast']['forecastday'][0]['day']
                save_weather_data(cursor, date, query, historical_weather, 'history')
                save_weather_data(cursor, date, query, data['forecast']['forecastday'][0]['astro'], 'astro')

        db_connection.commit()
        db_connection.close()

    def save_weather_data(cursor, date, location, weather, type):
        if type in ['current', 'history', 'forecast']:
            cursor.execute('''INSERT INTO weather_data (date, location, condition, condition_code, max_temp_c, min_temp_c, avg_temp_c,
                              max_wind_kph, total_precip_mm, total_snow_cm, avg_visibility_km, avg_humidity, will_it_rain, chance_of_rain,
                              will_it_snow, chance_of_snow, uv_index, recorded_time, temp_c, wind_kph, wind_degree, wind_dir, pressure_mb,
                              pressure_in, precip_mm, humidity, cloud, feels_like_c, wind_chill_c, heat_index_c, dew_point_c, visibility_km,
                              gust_kph)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (date, location, weather['condition']['text'], weather['condition']['code'],
                            weather.get('maxtemp_c'), weather.get('mintemp_c'), weather.get('avgtemp_c'),
                            weather.get('maxwind_kph'), weather.get('totalprecip_mm'), weather.get('totalsnow_cm', 0),
                            weather.get('avgvis_km'), weather.get('avghumidity'), 
                            'Yes' if weather.get('daily_will_it_rain', 0) else 'No', weather.get('daily_chance_of_rain', 0),
                            'Yes' if weather.get('daily_will_it_snow', 0) else 'No', weather.get('daily_chance_of_snow', 0),
                            weather.get('uv', 0), datetime.now().strftime('%Y-%m-%d %H:%M'), weather.get('temp_c'),
                            weather.get('wind_kph'), weather.get('wind_degree'), weather.get('wind_dir'),
                            weather.get('pressure_mb'), weather.get('pressure_in'), weather.get('precip_mm'),
                            weather.get('humidity'), weather.get('cloud'), weather.get('feelslike_c'), 
                            weather.get('windchill_c'), weather.get('heatindex_c'), weather.get('dewpoint_c'),
                            weather.get('vis_km'), weather.get('gust_kph')))
        elif type == 'astro':
            cursor.execute('''UPDATE weather_data SET sunrise=?, sunset=?, moonrise=?, moonset=?, moon_phase=?, moon_illumination=?,
                              is_moon_up=?, is_sun_up=?
                              WHERE date=? AND location=?''',
                           (weather['sunrise'], weather['sunset'], weather['moonrise'], weather['moonset'],
                            weather['moon_phase'], weather['moon_illumination'], 
                            weather.get('is_moon_up', 'No'), weather.get('is_sun_up', 'No'), date, location))

    with open('coords.txt', 'r') as file:
        coords = file.read().strip()
    api_key = "216de71353404ef899e162434242709"
    query = coords
    fetch_weather_data(api_key, query)

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

def schedule_tasks():
    while True:
        #
        now = datetime.now()
        
        next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
        
        time_to_wait = (next_minute - now).total_seconds()
        time.sleep(time_to_wait)
        
        solar_position_function()
        
        time.sleep(10)
        
        weathersql_function()
        weather_terminal_function()

if __name__ == "__main__":
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
        print("Program terminated by user.")
