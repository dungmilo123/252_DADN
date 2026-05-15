# umqtt_robust - MQTT client với reconnect (AITT-VN/yolobit_extension_mqtt)
import time
try:
    from .umqtt_simple import MQTTClient as _MQTTClientBase
except ImportError:
    from umqtt_simple import MQTTClient as _MQTTClientBase

class MQTTClient(_MQTTClientBase):

    DELAY = 2
    DEBUG = False

    def delay(self, i):
        time.sleep(self.DELAY)

    def log(self, in_reconnect, e):
        if self.DEBUG:
            if in_reconnect:
                print("mqtt reconnect: %r" % e)
            else:
                print("mqtt: %r" % e)

    def reconnect(self):
        i = 0
        start_time = time.ticks_ms()
        while (time.ticks_diff(time.ticks_ms(), start_time)) < 10000:
            try:
                return super().connect(False)
            except OSError as e:
                self.log(True, e)
            i += 1
            self.delay(i)

    def publish(self, topic, msg, retain=False, qos=0):
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 10000:
            try:
                return super().publish(topic, msg, retain, qos)
            except OSError as e:
                self.log(False, e)
                self.reconnect()

    def wait_msg(self):
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 10000:
            try:
                return super().wait_msg()
            except OSError as e:
                self.log(False, e)
                self.reconnect()
