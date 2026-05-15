# -*- coding: utf-8 -*-
"""
event_manager (polyfill) cho MicroPython/Yolo:Bit.

Một số firmware OhStem có sẵn module `event_manager`. Nếu firmware của bạn KHÔNG có,
file này cung cấp API tối thiểu để code (giống app OhStem sinh ra) vẫn chạy:

  from event_manager import *
  event_manager.reset()
  event_manager.add_timer_event(500, callback)
  while True:
      event_manager.run()
      time.sleep_ms(10)

Hỗ trợ:
- event_manager.reset()
- event_manager.add_timer_event(interval_ms, callback)  -> trả về id (int)
- event_manager.remove_timer_event(event_id)
- event_manager.run()
"""

import time


class _TimerEvent:
    __slots__ = ("id", "interval_ms", "callback", "next_ms", "enabled")

    def __init__(self, event_id, interval_ms, callback, next_ms):
        self.id = event_id
        self.interval_ms = int(interval_ms)
        self.callback = callback
        self.next_ms = next_ms
        self.enabled = True


class _EventManager:
    def __init__(self):
        self._events = []
        self._next_id = 1

    def reset(self):
        self._events = []
        self._next_id = 1

    def add_timer_event(self, interval_ms, callback):
        """
        Đăng ký callback chạy lặp lại theo chu kỳ interval_ms (milli giây).
        Trả về event_id để có thể remove nếu cần.
        """
        if callback is None:
            raise ValueError("callback is required")
        interval_ms = int(interval_ms)
        if interval_ms <= 0:
            raise ValueError("interval_ms must be > 0")

        now = time.ticks_ms()
        event_id = self._next_id
        self._next_id += 1

        ev = _TimerEvent(event_id, interval_ms, callback, time.ticks_add(now, interval_ms))
        self._events.append(ev)
        return event_id

    def remove_timer_event(self, event_id):
        """Xóa timer event theo id. Không lỗi nếu id không tồn tại."""
        for i, ev in enumerate(self._events):
            if ev.id == event_id:
                self._events.pop(i)
                return True
        return False

    def run(self):
        """
        Chạy các event đến hạn.
        Gọi trong vòng lặp chính (kèm sleep_ms nhỏ) để giống cách OhStem dùng.
        """
        if not self._events:
            return

        now = time.ticks_ms()
        for ev in self._events:
            if not ev.enabled:
                continue
            if time.ticks_diff(now, ev.next_ms) >= 0:
                # Reschedule trước để tránh drift khi callback chạy lâu
                ev.next_ms = time.ticks_add(ev.next_ms, ev.interval_ms)
                try:
                    ev.callback()
                except Exception as e:
                    # Không dừng toàn bộ scheduler nếu 1 task lỗi
                    print("event_manager callback error:", e)


# Export instance giống OhStem: event_manager.reset(), event_manager.run(), ...
event_manager = _EventManager()

__all__ = ["event_manager"]

