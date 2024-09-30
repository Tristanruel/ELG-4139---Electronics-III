import requests
import sqlite3
from datetime import datetime, timedelta

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

if __name__ == "__main__":
    with open('coords.txt', 'r') as file:
        coords = file.read().strip()
    api_key = "216de71353404ef899e162434242709"
    query = coords
    fetch_weather_data(api_key, query)
