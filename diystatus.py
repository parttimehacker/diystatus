#!/usr/bin/python3
""" Diyhas raspberry pi server status monitor """

import time
import socket
import paho.mqtt.client as mqtt
import psutil
from gpiozero import CPUTemperature

# Set up MQTT constants

MQTT_ADDRESS = "192.168.1.17"
HOST_NAME = socket.gethostname()
CPU_TOPIC = "diyhas/"+HOST_NAME+"/cpu"
CELSIUS_TOPIC = "diyhas/"+HOST_NAME+"/cpucelsius"
DISK_TOPIC = "diyhas/"+HOST_NAME+"/disk"

# done to overide pylint objections

DEBUG = False

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
        if DEBUG:
            print("CPU=",self.cpu_accumulator/self.iterations, "%")
            print("TMP=",self.celsius_accumulator/self.iterations, "C")
            print("DSK=",self.disk_free_accumulator/self.iterations, "GB")

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
    if msg.topic == 'diyhas/system/fire':
        if msg.payload == b'ON':
            print("fire message")
    elif msg.topic == 'diyhas/system/panic':
        if msg.payload == b'ON':
            print("panic message")
    elif msg.topic == 'diyhas/system/who':
        if msg.payload == b'ON':
            print("who message")

# use a dispatch model for the subscriptions
TOPIC_DISPATCH_DICTIONARY = {
    "diyhas/system/fire":
        {"method":system_message},
    "diyhas/system/panic":
        {"method":system_message},
    "diyhas/system/who":
        {"method":system_message}
    }

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rcdata):
    """ if we lose the connection & reconnect, subscriptions will be renewed """
    if DEBUG:
        print(userdata, flags, rcdata)
    client.subscribe("diyhas/system/fire", 1)
    client.subscribe("diyhas/system/panic", 1)
    client.subscribe("diyhas/system/who", 1)

def on_disconnect(client, userdata, rcdata):
    ''' optional disconnect method '''
    if DEBUG:
        print(userdata, rcdata)
    client.connected_flag = False
    client.disconnect_flag = True

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    """ dispatch to the appropriate MQTT topic handler """
    if DEBUG:
        print(client, userdata, msg)
    TOPIC_DISPATCH_DICTIONARY[msg.topic]["method"](msg)

if __name__ == '__main__':

    CLIENT = mqtt.Client()
    CLIENT.on_connect = on_connect
    CLIENT.on_disconnect = on_disconnect
    CLIENT.on_message = on_message
    CLIENT.connect(MQTT_ADDRESS, 1883, 60)
    CLIENT.loop_start()

    DATA_COLLECTOR = ServerDataCollector(CLIENT)

    # give network time to startup - hack?
    time.sleep(1.0)

    # loop forever checking for interrupts or timed events

    while True:
        time.sleep(10.0)
        DATA_COLLECTOR.collect_data()
        check_for_timed_events(DATA_COLLECTOR)
