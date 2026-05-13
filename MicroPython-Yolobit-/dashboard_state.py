# -*- coding: utf-8 -*-
"""Shared state and board controls for the local HTTP dashboard."""

import time

try:
    from yolobit import *
    _yolobit_ok = True
except Exception as e:
    _yolobit_ok = False
    _yolobit_err = e

try:
    from lib.aiot.aiot_dht20 import DHT20
    _dht_import_ok = True
except Exception as e:
    _dht_import_ok = False
    _dht_import_err = e


VALID_DISPLAY_MODES = ("off", "heart", "small_heart")

_dht20 = None
_last_sensor_ms = 0
_last_status_display_ms = 0
_status_toggle = False

state = {
    "boot_ms": 0,
    "wifi": "connecting",
    "ip": "",
    "display_mode": "heart",
    "button_a": False,
    "button_b": False,
    "dht20_present": False,
    "temperature": None,
    "humidity": None,
    "last_error": None,
}


def _ticks_ms():
    return time.ticks_ms()


def _ticks_diff(new, old):
    return time.ticks_diff(new, old)


def task_init():
    global _dht20, _last_sensor_ms
    print("[State] init start")
    if not _yolobit_ok:
        print("[State] yolobit import failed:", _yolobit_err)
    if not _dht_import_ok:
        print("[State] DHT20 import failed:", _dht_import_err)
    state["boot_ms"] = _ticks_ms()
    state["wifi"] = "connecting"
    state["ip"] = ""
    state["last_error"] = None
    _last_sensor_ms = 0
    update_buttons()
    _init_dht20()
    apply_display_mode()
    print("[State] init done, display_mode:", state["display_mode"])


def _init_dht20():
    global _dht20
    _dht20 = None
    state["dht20_present"] = False
    state["temperature"] = None
    state["humidity"] = None

    if not _dht_import_ok:
        set_error("DHT20 import failed: {}".format(_dht_import_err))
        return

    try:
        _dht20 = DHT20()
        state["dht20_present"] = True
        print("[Dashboard] DHT20 ready")
    except Exception as e:
        _dht20 = None
        state["dht20_present"] = False
        print("[Dashboard] DHT20 not available:", e)


def set_error(message):
    state["last_error"] = message
    if message:
        print("[Dashboard]", message)


def clear_error():
    state["last_error"] = None


def set_wifi(status, ip=""):
    state["wifi"] = status
    state["ip"] = ip or ""


def uptime_ms():
    return _ticks_diff(_ticks_ms(), state["boot_ms"])


def snapshot():
    update_buttons()
    data = {
        "wifi": state["wifi"],
        "ip": state["ip"],
        "uptime_ms": uptime_ms(),
        "display_mode": state["display_mode"],
        "button_a": state["button_a"],
        "button_b": state["button_b"],
        "dht20_present": state["dht20_present"],
        "temperature": state["temperature"],
        "humidity": state["humidity"],
        "last_error": state["last_error"],
    }
    return data


def update_buttons():
    if not _yolobit_ok:
        return
    try:
        state["button_a"] = bool(button_a.is_pressed())
        state["button_b"] = bool(button_b.is_pressed())
    except Exception as e:
        set_error("Button read failed: {}".format(e))


def update_sensors(interval_ms):
    global _last_sensor_ms
    update_buttons()
    now = _ticks_ms()
    if _last_sensor_ms and _ticks_diff(now, _last_sensor_ms) < interval_ms:
        return
    _last_sensor_ms = now

    if _dht20 is None:
        state["dht20_present"] = False
        state["temperature"] = None
        state["humidity"] = None
        return

    try:
        state["temperature"] = _dht20.dht20_temperature()
        state["humidity"] = _dht20.dht20_humidity()
        state["dht20_present"] = True
        print("[State] DHT20:", state["temperature"], "C", state["humidity"], "%")
    except Exception as e:
        state["temperature"] = None
        state["humidity"] = None
        state["dht20_present"] = False
        set_error("DHT20 read failed: {}".format(e))


def set_display_mode(mode):
    if mode not in VALID_DISPLAY_MODES:
        return False
    state["display_mode"] = mode
    if state["wifi"] == "connected":
        apply_display_mode()
    return True


def apply_display_mode():
    if not _yolobit_ok:
        return
    try:
        if state["display_mode"] == "off":
            if hasattr(display, "clear"):
                display.clear()
            else:
                display.show(Image("00000:00000:00000:00000:00000"))
        elif state["display_mode"] == "small_heart":
            display.show(Image.HEART_SMALL)
        else:
            display.show(Image.HEART)
    except Exception as e:
        set_error("Display update failed: {}".format(e))


def show_wifi_connecting():
    global _last_status_display_ms, _status_toggle
    if not _yolobit_ok:
        return
    now = _ticks_ms()
    if _last_status_display_ms and _ticks_diff(now, _last_status_display_ms) < 500:
        return
    _last_status_display_ms = now
    _status_toggle = not _status_toggle
    try:
        if _status_toggle:
            display.show(Image("00900:09990:99999:00900:00900"))
        else:
            display.show(Image("00000:00900:09990:00900:00000"))
    except Exception as e:
        set_error("Display status failed: {}".format(e))


def show_wifi_failed():
    if not _yolobit_ok:
        return
    try:
        display.show(Image("90009:09090:00900:09090:90009"))
    except Exception as e:
        set_error("Display failure status failed: {}".format(e))


def show_ip(ip):
    if not _yolobit_ok:
        return
    try:
        if hasattr(display, "scroll"):
            display.scroll(ip)
        else:
            display.show(Image.HEART)
    except Exception as e:
        set_error("Display IP failed: {}".format(e))
    apply_display_mode()
