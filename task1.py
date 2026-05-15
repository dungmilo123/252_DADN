# -*- coding: utf-8 -*-
"""
Task 1: In "Xin chào!" ra serial mỗi chu kỳ.
Mỗi task có 2 hàm: task_init() và task_run().
task_run() được đăng ký vào event_manager.add_timer_event().
"""

status = 0


def task_init():
    """Khởi tạo task 1 (chạy một lần khi bắt đầu chương trình)."""
    global status
    status = 0


def task_run():
    """Thực hiện task 1 mỗi lần được event_manager gọi (in ra serial)."""
    print("Xin chào!")
