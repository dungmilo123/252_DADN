# -*- coding: utf-8 -*-
"""
Task thu thập dữ liệu từ DHT20 — in CSV qua serial để PC ghi lại.
Dùng nút A trên Yolo:Bit để chuyển label (0 → 1 → 2 → 0 ...).
Dùng nút B để bật/tắt ghi mẫu.

Output serial dạng: DATA,<temp>,<humidity>,<label_name>
PC chạy ai/collect_data.py để đọc serial và lưu CSV.
"""
from yolobit import *
from lib.aiot.aiot_dht20 import DHT20

LABEL_NAMES = ["binh_thuong", "nong_am", "lanh_kho"]

_dht = None
_label_idx = 0
_recording = False
_btn_a_prev = False
_btn_b_prev = False


def task_init():
    global _dht
    try:
        _dht = DHT20()
        print("[Collect] DHT20 OK. Nhan A=doi label, B=bat/tat ghi.")
        print("[Collect] Label hien tai:", LABEL_NAMES[_label_idx])
    except Exception as e:
        print("[Collect] DHT20 loi:", e)
        _dht = None


def task_run():
    global _label_idx, _recording, _btn_a_prev, _btn_b_prev

    if _dht is None:
        return

    # Nút A: chuyển label
    btn_a = button_a.is_pressed()
    if btn_a and not _btn_a_prev:
        _label_idx = (_label_idx + 1) % len(LABEL_NAMES)
        print("[Collect] Label ->", LABEL_NAMES[_label_idx])
    _btn_a_prev = btn_a

    # Nút B: bật/tắt recording
    btn_b = button_b.is_pressed()
    if btn_b and not _btn_b_prev:
        _recording = not _recording
        print("[Collect] Recording:", "BAT" if _recording else "TAT")
    _btn_b_prev = btn_b

    if not _recording:
        return

    try:
        temp = _dht.dht20_temperature()
        hum = _dht.dht20_humidity()
        label = LABEL_NAMES[_label_idx]
        print("DATA,{:.1f},{:.1f},{}".format(temp, hum, label))
    except Exception as e:
        print("[Collect] Read error:", e)
