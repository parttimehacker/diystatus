# diystatus
Do It Yourself server status monitor for Raspberry Pi written in Python3. Computes CPU utilization as a percent, CPU temperature in celsius and free disk space in GB. 
- Publishes metrics every 10 minutes
- Uses host name to create MQTT topics

## Requires:
```
import time
import socket
import paho.mqtt.client as mqtt
import psutil
from gpiozero import CPUTemperature
```

## Install:
```
sudo pip3 install paho-mqtt
sudo pip3 install psutil
sudo apt install python3-gpiozero
```

## Useful utilities:
```
sudo pip3 install pylint
sudo apt -y install screen
```

## Setting up systemctl service

- It is a good idea to run diystatus.py as a system service at boot time
- Edit the diystatus.service file and enter your user directory 
- Enter the following commands to install the service
```
sudo cp diystatus.service /lib/systemd/system/diystatus.service
sudo chmod 644 /lib/systemd/system/diystatus.service
sudo systemctl daemon-reload
sudo systemctl enable diystatus.service
```
- Reboot is recommended
