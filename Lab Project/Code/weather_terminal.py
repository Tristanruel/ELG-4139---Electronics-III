import requests

def main():
    with open('coords.txt', 'r') as file:
        coords = file.read().strip()
    url = "http://api.weatherapi.com/v1/forecast.json"
    apiKey = "216de71353404ef899e162434242709"
    query = coords

    params = {
        'key': apiKey,
        'q': query,
        'days': 3  # Fetch forecast for the next 3 days
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

if __name__ == "__main__":
    main()
