import gpsd
from datetime import datetime, timedelta
import pytz
import ntplib
import pvlib
from pvlib.location import Location
from pvlib.solarposition import get_solarposition
import pandas as pd

def print_green(text):
    print(f"\033[92m{text}\033[0m")

def print_red(text):
    print(f"\033[91m{text}\033[0m")

try:
    gpsd.connect()
    print_green("GPSD connected successfully.")
except Exception as e:
    print_red("Failed to connect to GPSD.")
    raise SystemExit(e)

def get_ntp_time(ntp_server='time.google.com'):
    client = ntplib.NTPClient()
    response = client.request(ntp_server, version=3)
    ntp_time = datetime.utcfromtimestamp(response.tx_time)
    return ntp_time.replace(tzinfo=pytz.UTC)

try:
    packet = gpsd.get_current()
    if packet.mode < 2:
        raise ValueError("GPS fix not available")
    latitude = packet.lat
    longitude = packet.lon
    current_time = datetime.now(pytz.timezone('America/New_York')).replace(microsecond=0)
except Exception as e:
    print_red(str(e))
    print_red("Continuing with backup coordinates and NTP time...")
    latitude, longitude = 45.365977, -75.602712
    current_time = get_ntp_time()

print_green(f"\nCurrent local date and time: {current_time}")
print_green(f"Current GPS coordinates: Latitude {latitude}, Longitude {longitude}")

site = Location(latitude, longitude, tz='America/New_York')
start_time = current_time
end_time = start_time + timedelta(days=1)
times_range = pd.date_range(start=start_time, end=end_time, freq='1s', tz=site.tz)
solar_pos = get_solarposition(times_range, latitude, longitude)

# Find the first time sun is at or just above 10 degrees elevation
sun_at_10 = solar_pos[solar_pos['elevation'] >= 10]
if not sun_at_10.empty:
    first_time_at_10 = sun_at_10.index[0]
    time_until_sun_at_10 = first_time_at_10 - current_time
    if time_until_sun_at_10.total_seconds() > 0:
        countdown_message = f"Time until the sun is 10 degrees above the horizon: {time_until_sun_at_10}\n"
        seconds_until_sun_at_10 = int(time_until_sun_at_10.total_seconds())
        print_green(countdown_message)
        with open("countdown.txt", "w") as file:
            file.write(str(seconds_until_sun_at_10))
    else:
        print_red("The sun was 10 degrees above the horizon earlier today.\n")
else:
    print_red("No time today when the sun reaches 10 degrees elevation.\n")

# Output the first and last line of data
if not sun_at_10.empty:
    with open("10degsun.txt", "w") as file:
        file.write(sun_at_10.head(1).to_string() + '\n')  # First line
        file.write(sun_at_10.tail(1).to_string())  # Last line

print(sun_at_10)
