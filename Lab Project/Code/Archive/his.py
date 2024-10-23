import requests
from datetime import datetime, timedelta

def main():
    url = "http://api.weatherapi.com/v1/history.json"
    apiKey = "216de71353404ef899e162434242709"  # Replace with your actual API key
    query = "45.419847,-75.679463"

    # Get dates for the last 3 days
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 2)]

    for date in dates:
        params = {
            'key': apiKey,
            'q': query,
            'dt': date
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            json_data = response.json()

            # Extract location information
            location_data = json_data['location']
            location = f"{location_data['region']}, {location_data['name']}, {location_data['country']}"
            localtime_epoch = location_data['localtime_epoch']
            localtime = location_data['localtime']

            # Print location information
            print(f"\nWeather data for '{location}' on {date}")
            print(f"Local Time: {localtime} (Epoch: {localtime_epoch})")

            # Extract forecast data for the date
            forecast_day = json_data['forecast']['forecastday'][0]
            date_epoch = forecast_day['date_epoch']
            day_data = forecast_day['day']
            astro = forecast_day['astro']
            hour_data = forecast_day['hour']

            # Extract all day_data variables
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
            totalsnow_cm = day_data.get('totalsnow_cm', None)
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

            # Astro data
            sunrise = astro['sunrise']
            sunset = astro['sunset']
            moonrise = astro['moonrise']
            moonset = astro['moonset']
            moon_phase = astro['moon_phase']
            moon_illumination = astro['moon_illumination']
            # Note: 'is_moon_up' and 'is_sun_up' may not be available in historical data

            # Print day data
            print(f"\nDate Epoch: {date_epoch}")
            print(f"Condition: {condition_text}")
            print(f"Condition Icon: {condition_icon}")
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

            # Astro data
            print("\nAstro Data:")
            print(f"  Sunrise: {sunrise}")
            print(f"  Sunset: {sunset}")
            print(f"  Moonrise: {moonrise}")
            print(f"  Moonset: {moonset}")
            print(f"  Moon Phase: {moon_phase}")
            print(f"  Moon Illumination: {moon_illumination}%")

            # Hourly data
            print("\nHourly Data:")
            for hour in hour_data:
                time_epoch = hour['time_epoch']
                time = hour['time']
                temp_c = hour['temp_c']
                temp_f = hour['temp_f']
                is_day = hour['is_day']
                condition_text = hour['condition']['text']
                condition_icon = hour['condition']['icon']
                condition_code = hour['condition']['code']
                wind_mph = hour['wind_mph']
                wind_kph = hour['wind_kph']
                wind_degree = hour['wind_degree']
                wind_dir = hour['wind_dir']
                pressure_mb = hour['pressure_mb']
                pressure_in = hour['pressure_in']
                precip_mm = hour['precip_mm']
                precip_in = hour['precip_in']
                humidity = hour['humidity']
                cloud = hour['cloud']
                feelslike_c = hour['feelslike_c']
                feelslike_f = hour['feelslike_f']
                windchill_c = hour.get('windchill_c', None)
                windchill_f = hour.get('windchill_f', None)
                heatindex_c = hour.get('heatindex_c', None)
                heatindex_f = hour.get('heatindex_f', None)
                dewpoint_c = hour['dewpoint_c']
                dewpoint_f = hour['dewpoint_f']
                will_it_rain = hour['will_it_rain']
                chance_of_rain = hour['chance_of_rain']
                will_it_snow = hour['will_it_snow']
                chance_of_snow = hour['chance_of_snow']
                vis_km = hour['vis_km']
                vis_miles = hour['vis_miles']
                gust_mph = hour['gust_mph']
                gust_kph = hour['gust_kph']
                uv = hour['uv']

                print(f"\nTime: {time} (Epoch: {time_epoch})")
                print(f"  Temperature: {temp_c}°C / {temp_f}°F")
                print(f"  Condition: {condition_text}")
                print(f"  Is Day: {'Yes' if is_day else 'No'}")
                print(f"  Wind: {wind_kph} kph / {wind_mph} mph, Direction: {wind_dir} ({wind_degree}°)")
                print(f"  Pressure: {pressure_mb} mb / {pressure_in} in")
                print(f"  Precipitation: {precip_mm} mm / {precip_in} in")
                print(f"  Humidity: {humidity}%")
                print(f"  Cloud Cover: {cloud}%")
                print(f"  Feels Like: {feelslike_c}°C / {feelslike_f}°F")
                if windchill_c is not None:
                    print(f"  Wind Chill: {windchill_c}°C / {windchill_f}°F")
                if heatindex_c is not None:
                    print(f"  Heat Index: {heatindex_c}°C / {heatindex_f}°F")
                print(f"  Dew Point: {dewpoint_c}°C / {dewpoint_f}°F")
                print(f"  Will it rain?: {'Yes' if will_it_rain else 'No'}")
                print(f"  Chance of rain: {chance_of_rain}%")
                print(f"  Will it snow?: {'Yes' if will_it_snow else 'No'}")
                print(f"  Chance of snow: {chance_of_snow}%")
                print(f"  Visibility: {vis_km} km / {vis_miles} miles")
                print(f"  Gust Speed: {gust_kph} kph / {gust_mph} mph")
                print(f"  UV Index: {uv}")

        else:
            print(f"Failed to retrieve weather data for {date}. HTTP status code: {response.status_code}")

if __name__ == "__main__":
    main()
