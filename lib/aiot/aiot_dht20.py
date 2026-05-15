# -*- coding: utf-8 -*-
# DHT20 - cảm biến nhiệt độ, độ ẩm (AIOT KIT OhStem). Nguồn: AITT-VN/yolobit_extension_aiot
# Cần: yolobit (pin19, pin20), machine.SoftI2C, Pin
from yolobit import *
from machine import SoftI2C, Pin
from time import sleep_ms

class DHT20(object):
    def __init__(self):
        self.i2c = SoftI2C(scl=Pin(pin19.pin), sda=Pin(pin20.pin))
        if (self.dht20_read_status() & 0x80) == 0x80:
            self.dht20_init()

    def read_dht20(self):
        self.i2c.writeto(0x38, bytes([0xac, 0x33, 0x00]))
        sleep_ms(80)
        cnt = 0
        while (self.dht20_read_status() & 0x80) == 0x80:
            sleep_ms(1)
            if cnt >= 100:
                break
            cnt += 1
        data = self.i2c.readfrom(0x38, 7, True)
        return list(data)

    def dht20_read_status(self):
        data = self.i2c.readfrom(0x38, 1, True)
        return data[0]

    def dht20_init(self):
        self.i2c.writeto(0x38, bytes([0xa8, 0x00, 0x00]))
        sleep_ms(10)
        self.i2c.writeto(0x38, bytes([0xbe, 0x08, 0x00]))

    def dht20_temperature(self):
        data = self.read_dht20()
        temper = (data[3] << 16) | (data[4] << 8) | data[5]
        temper = temper & 0xfffff
        return round((temper * 200 * 10 / 1024 / 1024 - 500) / 10, 1)

    def dht20_humidity(self):
        data = self.read_dht20()
        humidity = (data[1] << 16) | (data[2] << 8) | data[3]
        humidity = humidity >> 4
        return round((humidity * 100 * 10 / 1024 / 1024) / 10, 1)
