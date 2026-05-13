# -*- coding: utf-8 -*-
"""
Task 2: Chớp tắt đèn / hình trên màn hình (HEART và HEART_SMALL).
Code tương tự block kéo thả OhStem: status đảo 0/1, hiển thị Image.HEART hoặc Image.HEART_SMALL.
Mỗi task có 2 hàm: task_init() và task_run().
"""

from yolobit import *

status = 0


def task_init():
    """Khởi tạo task 2 (chạy một lần khi bắt đầu chương trình)."""
    global status
    status = 0


def task_run():
    """Chớp tắt giữa hình trái tim lớn và nhỏ trên display (code chớp tắt đèn)."""
    global status
    status = 1 - status
    if status == 0:
        display.show(Image.HEART)
    else:
        display.show(Image.HEART_SMALL)
