#!/bin/bash
# run by: 
# chmod +x install_libraries.sh
# ./install_libraries.sh
sudo apt update
sudo apt install -y libhdf5-dev chrony pps-tools gpsd gpsd-clients python3-gps python3 python3-pip

if [[ "$VIRTUAL_ENV" != "" ]]
then
    pip install gpsd-py3 ntplib pvlib pandas pytz h5py RPi.GPIO timezonefinder requests Adafruit_CircuitPython_DHT
else
    sudo pip3 install gpsd-py3 ntplib pvlib pandas pytz h5py RPi.GPIO timezonefinder requests Adafruit_CircuitPython_DHT
fi

sudo dpkg-reconfigure gpsd
