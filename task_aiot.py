# -*- coding: utf-8 -*-
"""
Task AIOT – Kiểm thử thư viện lib.aiot (DHT20, RGBLed).
Cần phần cứng AIOT KIT (DHT20 I2C pin19/20, hoặc NeoPixel). Nếu không có cảm biến, vẫn in "[AIOT] lib OK".
"""
try:
    from lib.aiot.aiot_dht20 import DHT20
    _dht_ok = True
except Exception as e:
    _dht_ok = False
    _dht_err = e

try:
    from lib.aiot.aiot_rgbled import RGBLed
    from yolobit import *
    _rgb_ok = True
except Exception as e:
    _rgb_ok = False
    _rgb_err = e

dht = None
rgb = None
_rgb_index = 0
_aiot_tick = 0


def task_init():
    """Khởi tạo DHT20 (nếu có) và RGBLed (nếu có yolobit pin)."""
    global dht, rgb
    if _dht_ok:
        try:
            dht = DHT20()
        except OSError as e:
            if e.args[0] == 19:  # ENODEV
                print("[AIOT] DHT20: chua cam cam bien hoac sai chan I2C (pin19/20)")
            else:
                print("[AIOT] DHT20:", e)
            dht = None
        except Exception as e:
            print("[AIOT] DHT20:", e)
            dht = None
    else:
        print("[AIOT] DHT20 import:", _dht_err)
    if _rgb_ok:
        try:
            rgb = RGBLed(pin14.pin, 4)  # 4 LED, pin14 (tùy board)
        except Exception as e:
            print("[AIOT] RGBLed:", e)
            rgb = None
    else:
        print("[AIOT] RGBLed import:", _rgb_err if '_rgb_err' in dir() else "yolobit/pin chua co")


def task_run():
    """Mỗi chu kỳ: đọc DHT20 (nếu có) hoặc chớp RGB (nếu có), hoặc in lib OK (không flood)."""
    global _rgb_index, _aiot_tick
    _aiot_tick += 1
    if dht:
        try:
            t = dht.dht20_temperature()
            h = dht.dht20_humidity()
            print("[AIOT] DHT20: {:.1f}C, {:.1f}%".format(t, h))
        except Exception as e:
            print("[AIOT] DHT20 read:", e)
    elif rgb:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        rgb.show((_rgb_index % 3) + 1, colors[_rgb_index % 3])
        _rgb_index += 1
    elif _dht_ok or _rgb_ok:
        if _aiot_tick % 5 == 1:
            print("[AIOT] lib OK (khong co cam bien/pin)")
