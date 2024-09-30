#chmod +x os.sh
#./os.sh

#!/bin/bash
# Enabling and starting the GPSD service
sudo systemctl enable gpsd
sudo systemctl start gpsd

# Running the Python script
python3 os.py
