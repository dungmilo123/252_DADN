# -*- coding: utf-8 -*-
# Event manager chính thức OhStem (Sự kiện) - nguồn AITT-VN/yolobit_extension_events
# Hỗ trợ: add_timer_event, add_message_event, add_condition_event, broadcast_message.
# Gọi run() trong vòng lặp chính. Callback có thể chạy trong thread (_thread).
import time
import _thread

_EVENT_TIMER = 0
_EVENT_MESSAGE = 1
_EVENT_CONDITION = 2

class EventManager:
    def __init__(self):
        self._events = []
        self._ticks = time.ticks_ms()

    def add_timer_event(self, interval, callback):
        if interval is None or interval <= 0 or callback is None:
            return
        self._events.append({"type": _EVENT_TIMER, "last_ticks": 0, "interval": interval, "callback": callback})

    def add_condition_event(self, condition, callback):
        if condition is None or callback is None:
            return
        self._events.append({"type": _EVENT_CONDITION, "condition": condition, "callback": callback})

    def add_message_event(self, message_index, callback):
        if message_index is None or message_index < 0 or callback is None:
            return
        self._events.append({"type": _EVENT_MESSAGE, "message_index": message_index, "callback": callback})

    def run(self):
        self._ticks = time.ticks_ms()
        for event in self._events:
            if self._check_event(event):
                self._run_event(event)

    def broadcast_message(self, message_index):
        for event in self._events:
            if event.get('type') == _EVENT_MESSAGE and event.get('message_index') == message_index:
                self._run_event(event)

    def _check_event(self, event):
        if event.get('type') == _EVENT_TIMER:
            if (self._ticks - event.get('last_ticks')) >= event.get('interval'):
                event['last_ticks'] = self._ticks
                return True
        elif event.get('type') == _EVENT_CONDITION and event.get('condition') is not None:
            return event.get('condition')()
        return False

    def _run_event(self, event):
        if event.get('callback') is not None:
            try:
                _thread.start_new_thread(event.get('callback'), ())
            except Exception:
                event.get('callback')()

    def reset(self):
        self._events = []

event_manager = EventManager()
