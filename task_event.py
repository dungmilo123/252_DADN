# -*- coding: utf-8 -*-
"""
Task Event – Kiểm thử thư viện lib.event_manager_ohstem (Sự kiện: message, broadcast).
Dùng add_message_event và broadcast_message để xác nhận thư viện hoạt động.
"""
try:
    from lib.event_manager_ohstem import event_manager as ev_ohstem
    _ev_ok = True
except Exception as e:
    _ev_ok = False
    _ev_err = e

_count = 0


def _on_message_0():
    print("[Event] nhan message 0 (lib.event_manager_ohstem)")


def task_init():
    """Đăng ký callback cho message 0."""
    global _count
    _count = 0
    if not _ev_ok:
        print("[Event] import loi:", _ev_err)
        return
    ev_ohstem.add_message_event(0, _on_message_0)


def task_run():
    """Mỗi chu kỳ: gửi broadcast message 0 để kích hoạt callback (kiểm thử lib)."""
    global _count
    if not _ev_ok:
        return
    _count += 1
    ev_ohstem.broadcast_message(0)
