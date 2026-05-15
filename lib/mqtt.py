# -*- coding: utf-8 -*-
# MQTT (OhStem) - nguồn AITT-VN/yolobit_extension_mqtt
# Cách dùng: from lib.mqtt import mqtt  (sau khi sync thư mục lib lên board)
import time
try:
    from .umqtt_robust import MQTTClient
    from .utility import *
except ImportError:
    from umqtt_robust import MQTTClient
    from utility import *

import ubinascii
import machine
import network

class MQTT:

    def __init__(self):
        self.client = None
        self.server = ''
        self.username = ''
        self.password = ''
        self.topic_prefix = ''
        self.message = ''
        self.topic = ''
        self.wifi_ssid = ''
        self.wifi_password = ''
        self.callbacks = {}
        self.last_sent = 0
        self.station = None  # chỉ có sau khi gọi connect_wifi()

    def __on_receive_message(self, topic, msg):
        msg = msg.decode('ascii')
        topic = topic.decode('ascii')
        if callable(self.callbacks.get(topic)):
            self.callbacks.get(topic)(msg)

    def connect_wifi(self, ssid, password, wait_for_connected=True):
        self.wifi_ssid = ssid
        self.wifi_password = password
        say('Connecting to WiFi...')
        self.station = network.WLAN(network.STA_IF)
        if self.station.active():
            self.station.active(False)
        time.sleep_ms(500)

        for i in range(5):
            try:
                self.station.active(True)
                self.station.connect(ssid, password)
                break
            except OSError:
                self.station.active(False)
                time.sleep_ms(500)
            if i == 4:
                say('Failed to connect to WiFi')
                raise Exception('Failed to connect to WiFi')

        if wait_for_connected:
            count = 0
            while self.station.isconnected() == False:
                count = count + 1
                if count > 150:
                    say('Failed to connect to WiFi')
                    raise Exception('Failed to connect to WiFi')
                time.sleep_ms(100)

        say('Wifi connected. IP:' + self.station.ifconfig()[0])

    def wifi_connected(self):
        if self.station is None:
            return False
        return self.station.isconnected()

    def connect_broker(self, server='mqtt.ohstem.vn', port=1883, username='', password=''):
        client_id = str(ubinascii.hexlify(machine.unique_id())) + str(time.ticks_ms())
        self.client = MQTTClient(client_id, server, port, username, password)
        try:
            self.client.disconnect()
        except Exception:
            pass
        self.client.connect()
        self.client.set_callback(self.__on_receive_message)
        self.server = server
        self.username = username
        self.password = password
        if server.lower() == 'mqtt.ohstem.vn' or server.lower() == 'io.adafruit.com':
            self.topic_prefix = '{:s}/feeds/'.format(self.username)
        else:
            self.topic_prefix = ''
        say('Connected to MQTT broker')

    def check_message(self):
        if self.client is None:
            return
        if not self.wifi_connected():
            say('WiFi disconnected. Reconnecting...')
            self.connect_wifi(self.wifi_ssid, self.wifi_password)
            self.client.connect()
            self.resubscribe()

        self.client.check_msg()

    def on_receive_message(self, topic, callback):
        if self.client is None:
            return
        topic = self.topic_prefix + str(topic)
        self.callbacks[topic] = callback
        self.client.subscribe(topic)

    def resubscribe(self):
        for key in self.callbacks.keys():
            self.client.subscribe(key)

    def publish(self, topic, message):
        if self.client is None:
            return
        now = time.ticks_ms()
        if now - self.last_sent < 1000:
            time.sleep_ms(1000 - (now - self.last_sent))
        topic = self.topic_prefix + str(topic)
        self.client.publish(topic, str(message))
        self.last_sent = time.ticks_ms()

mqtt = MQTT()
