# -*- coding: utf-8 -*-
"""
Task AI Chạy inference Tiny NN trên Yolo:Bit.
Đọc DHT20 (nhiệt độ, độ ẩm) → chạy predict() → in kết quả phân loại.
Cần: model.py (đã export từ ai/export_model.py) và inference.py.
"""
from lib.aiot.aiot_dht20 import DHT20

_dht = None
_inference_ok = False
_tick = 0

try:
    from inference import predict
    _inference_ok = True
except Exception as e:
    print("[AI] import inference loi:", e)


def task_init():
    global _dht
    if not _inference_ok:
        print("[AI] Khong the chay: kiem tra model.py va inference.py")
        return
    try:
        _dht = DHT20()
        print("[AI] DHT20 + inference OK, san sang.")
    except Exception as e:
        print("[AI] DHT20 loi:", e, "- se dung gia tri gia.")
        _dht = None


def task_run():
    global _tick
    if not _inference_ok:
        return

    _tick += 1

    if _dht:
        try:
            temp = _dht.dht20_temperature()
            hum = _dht.dht20_humidity()
        except Exception:
            temp, hum = 25.0, 55.0
    else:
        # Không có DHT20: dùng giá trị tự tạo thay đổi để demo
        temp = 20.0 + (_tick % 30)
        hum = 30.0 + (_tick % 50)

    label, confidence, scores = predict(temp, hum)
    print("[AI] {:.1f}C {:.1f}% -> {} (conf={:.2f})".format(temp, hum, label, confidence))
