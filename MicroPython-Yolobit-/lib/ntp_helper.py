# -*- coding: utf-8 -*-
"""
NTP helper - lấy thời gian theo internet (giống block NTP của OhStem).
Cần kết nối WiFi trước (ví dụ: mqtt.connect_wifi() hoặc wifi từ firmware).
Cách dùng: from lib.ntp_helper import set_time_from_ntp, get_time
"""
import time

def set_time_from_ntp(gmt_offset=7):
    """
    Đồng bộ thời gian từ NTP và áp dụng múi giờ (mặc định GMT+7 Việt Nam).
    Gọi sau khi đã kết nối WiFi.
    gmt_offset: +7 (VN), +8, -5, ...
    """
    try:
        import ntptime
        from machine import RTC
    except ImportError:
        print("ntp_helper: ntptime hoac machine.RTC khong co")
        return False
    try:
        ntptime.settime()
    except Exception as e:
        print("ntp_helper settime error:", e)
        return False
    rtc = RTC()
    try:
        # RTC().datetime() -> (year, month, day, weekday, hour, minute, second, subsecond)
        t = rtc.datetime()
    except Exception:
        t = time.gmtime()
        # gmtime returns (year, month, mday, hour, minute, second, weekday, yearday)
        t = (t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0)
    year, month, mday, weekday, hour, minute, second = t[0], t[1], t[2], t[3], t[4], t[5], t[6]
    try:
        subsecond = t[7] if len(t) > 7 else 0
    except Exception:
        subsecond = 0
    hour = hour + gmt_offset
    if hour >= 24:
        hour -= 24
        mday += 1
    elif hour < 0:
        hour += 24
        mday -= 1
    rtc.init((year, month, mday, weekday, hour, minute, second, subsecond))
    return True

def get_time():
    """
    Trả về (year, month, day, hour, minute, second) từ RTC.
    Gọi set_time_from_ntp() ít nhất một lần (sau khi có WiFi) trước khi dùng.
    """
    try:
        from machine import RTC
        t = RTC().datetime()
        return (t[0], t[1], t[2], t[4], t[5], t[6])
    except Exception:
        return (2000, 1, 1, 0, 0, 0)

def get_time_str():
    """Trả về chuỗi dạng "YYYY-MM-DD HH:MM:SS"."""
    t = get_time()
    return "%04d-%02d-%02d %02d:%02d:%02d" % (t[0], t[1], t[2], t[3], t[4], t[5])
