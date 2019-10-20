# diystatus
Do It Yourself Home Automation System server status monitor for Raspberry Pi written in Python3.
- Computes CPU utilization, CPU temperature in celsius and free disk space in GB. 
- Publishes every 10 minutes
- Requires 
```
import time
import socket
import paho.mqtt.client as mqtt
import psutil
from gpiozero import CPUTemperature
```
- Install
```
sudo pip3 install psutil
sudo apt install python3-gpiozero
```
- Useful utilities
```
sudo pip3 install pylint
sudo apt -y install screen
```

