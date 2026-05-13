# -*- coding: utf-8 -*-
"""
Task MQTT – Kiểm thử thư viện lib.mqtt (WiFi + MQTT).
Cần cấu hình WIFI_SSID, WIFI_PASSWORD (và tùy chọn MQTT) trong config.py.
Nếu chưa cấu hình WiFi, task vẫn chạy và in "[MQTT] lib OK" để xác nhận import thành công.
"""
try:
    from lib.mqtt import mqtt
    _mqtt_ok = True
except Exception as e:
    _mqtt_ok = False
    _mqtt_err = e

status = 0


def task_init():
    """Khởi tạo: nếu có WiFi trong config thì kết nối (không bắt buộc)."""
    global status
    status = 0
    if not _mqtt_ok:
        print("[MQTT] import loi:", _mqtt_err)
        return
    try:
        import config
        if getattr(config, 'WIFI_SSID', None) and getattr(config, 'WIFI_PASSWORD', None):
            mqtt.connect_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
            if getattr(config, 'MQTT_SERVER', None):
                mqtt.connect_broker(
                    server=getattr(config, 'MQTT_SERVER', 'mqtt.ohstem.vn'),
                    port=getattr(config, 'MQTT_PORT', 1883),
                    username=getattr(config, 'MQTT_USER', ''),
                    password=getattr(config, 'MQTT_PASSWORD', ''),
                )
    except Exception as e:
        print("[MQTT] init:", e)


def task_run():
    """Mỗi chu kỳ: gọi check_message() và in trạng thái (kiểm thử lib hoạt động)."""
    global status
    if not _mqtt_ok:
        return
    mqtt.check_message()
    status += 1
    if status % 10 == 1:  # Mỗi 10 lần in 1 lần
        if mqtt.wifi_connected():
            print("[MQTT] OK, wifi connected")
        else:
            print("[MQTT] lib OK (chua ket noi WiFi)")
