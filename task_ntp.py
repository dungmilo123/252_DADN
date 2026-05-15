# -*- coding: utf-8 -*-
"""
Task NTP – Kiểm thử thư viện lib.ntp_helper (đồng bộ thời gian).
Cần WiFi (ví dụ từ task_mqtt hoặc cấu hình trước). Lần đầu gọi set_time_from_ntp(7) trong task_init nếu có WiFi.
"""
try:
    from lib.ntp_helper import set_time_from_ntp, get_time_str
    _ntp_ok = True
except Exception as e:
    _ntp_ok = False
    _ntp_err = e

_ntp_done = False


def task_init():
    """Thử đồng bộ NTP một lần nếu có WiFi (qua mqtt hoặc network)."""
    global _ntp_done
    if not _ntp_ok:
        print("[NTP] import loi:", _ntp_err)
        return
    try:
        from lib.mqtt import mqtt
        if mqtt.wifi_connected():
            if set_time_from_ntp(7):
                print("[NTP] da dong bo gio")
                _ntp_done = True
            else:
                print("[NTP] dong bo that bai")
        else:
            print("[NTP] lib OK (chua co WiFi)")
    except Exception as e:
        print("[NTP] init:", e)


def task_run():
    """Mỗi chu kỳ: in thời gian RTC (get_time_str)."""
    if not _ntp_ok:
        return
    print("[NTP]", get_time_str())
