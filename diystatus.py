#!/usr/bin/python3
""" Diyhas raspberry pi server status monitor """

import time
import socket
import logging
import logging.config
import subprocess

import paho.mqtt.client as mqtt
import psutil
from gpiozero import CPUTemperature

# Set up MQTT constants

MQTT_ADDRESS = "192.168.1.53"
HOST_NAME = socket.gethostname()
CPU_TOPIC = "diy/"+HOST_NAME+"/cpu"
CELSIUS_TOPIC = "diy/"+HOST_NAME+"/cpucelsius"
DISK_TOPIC = "diy/"+HOST_NAME+"/disk"
OS_VERSION_TOPIC = "diy/"+HOST_NAME+"/os"
PI_VERSION_TOPIC = "diy/"+HOST_NAME+"/pi"

# done to overide pylint objections

logging.config.fileConfig(fname='/home/an/diystatus/logging.ini', disable_existing_loggers=False)

# Get the logger specified in the file
LOGGER = logging.getLogger("diystatus")

LOGGER.info('Application started')

class ServerDataCollector():
    ''' class to encapuslate data collection '''
    def __init__(self, client):
        ''' server system status monitor with MQTT reporting '''
        self.client = client
        self.host = socket.gethostname()
        self.cpu_accumulator = 0.0
        self.celsius_accumulator = 0.0
        self.disk_free_accumulator = 0.0
        self.iterations = 0.0

    def collect_data(self,):
        ''' collect one sample of data '''
        self.cpu_accumulator += psutil.cpu_percent(interval=1)
        cpu = CPUTemperature()
        self.celsius_accumulator += cpu.temperature
        disk = psutil.disk_usage('/')
        # Divide from Bytes -> KB -> MB -> GB
        self.disk_free_accumulator += round(disk.free/1024.0/1024.0/1024.0, 1)
        self.iterations += 1.0

    def publish_averages(self,):
        ''' publish cpu temperature and free in to MQTT '''
        if self.iterations > 0:
            cpu = self.cpu_accumulator / self.iterations
            celsius = self.celsius_accumulator  / self.iterations
            free = self.disk_free_accumulator / self.iterations
            info = "{0:.1f}".format(cpu)
            self.client.publish(CPU_TOPIC, str(info), 0, True)
            info = "{0:.1f}".format(celsius)
            self.client.publish(CELSIUS_TOPIC, str(info), 0, True)
            info = "{0:.1f}".format(free)
            self.client.publish(DISK_TOPIC, str(info), 0, True)
            self.cpu_accumulator = 0.0
            self.celsius_accumulator = 0.0
            self.disk_free_accumulator = 0.0
            self.iterations = 0.0
            
def publish_os_version(client):
    ''' get the current os version and make available to diyservers '''
    cmd = subprocess.Popen('cat /etc/os-release', shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
        if b'=' in line:
            key, value = line.split(b'=')
            if b'VERSION' == key:
                data, chaff = value.split(b'\n')
                strData = str(data, 'utf-8')
                osVersion = strData.replace('"','')
                client.publish(OS_VERSION_TOPIC, osVersion, 0, True)
                
def publish_pi_version(client):
    ''' get the current pi version and make available to diyservers '''
    cmd = subprocess.Popen('cat /proc/device-tree/model', shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
        key, value = line.split(b' Pi ')
        data, chaff = value.split(b'\x00')
        piVersion = str(data, 'utf-8') + "Raspberry Pi "
        client.publish(PI_VERSION_TOPIC, piVersion, 0, True)

def check_system_status(data_collector):
    ''' display systems status '''
    data_collector.publish_averages()

def last_timed_event():
    ''' reset the timed events dictionary '''
    for key in TIMED_EVENTS_DICTIONARY:
        TIMED_EVENTS_DICTIONARY[key]["executed"] = False

TIMED_EVENTS_DICTIONARY = {
    "01": {"method":check_system_status, "executed":False},
    "11": {"method":check_system_status, "executed":False},
    "21": {"method":check_system_status, "executed":False},
    "31": {"method":check_system_status, "executed":False},
    "41": {"method":check_system_status, "executed":False},
    "51": {"method":check_system_status, "executed":False}
    }

def check_for_timed_events(data_collector):
    ''' see if its time to capture and publish metrics '''
    minute_string = time.strftime("%M")
    if minute_string == "59":
        last_timed_event()
    elif minute_string in TIMED_EVENTS_DICTIONARY:
        if not TIMED_EVENTS_DICTIONARY[minute_string]["executed"]:
            TIMED_EVENTS_DICTIONARY[minute_string]["executed"] = True
            TIMED_EVENTS_DICTIONARY[minute_string]["method"](data_collector)

def system_message(msg):
    """ process system messages"""
    if msg.topic == 'diy/system/fire':
        if msg.payload == b'ON':
            print("fire message")
    elif msg.topic == 'diy/system/panic':
        if msg.payload == b'ON':
            print("panic message")
    elif msg.topic == 'diy/system/who':
        if msg.payload == b'ON':
            print("who message")

# use a dispatch model for the subscriptions
TOPIC_DISPATCH_DICTIONARY = {
    "diy/system/fire":
        {"method":system_message},
    "diy/system/panic":
        {"method":system_message},
    "diy/system/who":
        {"method":system_message}
    }

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rcdata):
    """ if we lose the connection & reconnect, subscriptions will be renewed """
    client.subscribe("diy/system/fire", 1)
    client.subscribe("diy/system/panic", 1)
    client.subscribe("diy/system/who", 1)

def on_disconnect(client, userdata, rcdata):
    ''' optional disconnect method '''
    client.connected_flag = False
    client.disconnect_flag = True

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    """ dispatch to the appropriate MQTT topic handler """
    TOPIC_DISPATCH_DICTIONARY[msg.topic]["method"](msg)

if __name__ == '__main__':

    CLIENT = mqtt.Client()
    CLIENT.on_connect = on_connect
    CLIENT.on_disconnect = on_disconnect
    CLIENT.on_message = on_message
    CLIENT.connect(MQTT_ADDRESS, 1883, 60)
    CLIENT.loop_start()
    
    publish_os_version(CLIENT)
    publish_pi_version(CLIENT)

    DATA_COLLECTOR = ServerDataCollector(CLIENT)

    # give network time to startup - hack?
    time.sleep(1.0)

    # loop forever checking for interrupts or timed events

    while True:
        time.sleep(10.0)
        DATA_COLLECTOR.collect_data()
        check_for_timed_events(DATA_COLLECTOR)
