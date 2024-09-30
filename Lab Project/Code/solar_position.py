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

# Set default coordinates and timezone
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