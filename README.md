# diystatus
Do It Yourself server status monitor for Raspberry Pi written in Python3. Computes CPU utilization as a percent, CPU temperature in celsius and free disk space in GB. 
- Publishes metrics every 10 minutes
- Uses host name to create MQTT topics

- Requires:
```
import time
import socket
import paho.mqtt.client as mqtt
import psutil
from gpiozero import CPUTemperature
```

- Install:
```
sudo pip3 install paho-mqtt
sudo pip3 install psutil
sudo apt install python3-gpiozero
```

- Useful utilities:
```
sudo pip3 install pylint
sudo apt -y install screen
```
