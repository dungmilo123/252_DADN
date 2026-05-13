# -*- coding: utf-8 -*-
"""
Yolo:Bit board-hosted HTTP dashboard.

Default boot path:
- join the configured Wi-Fi network in STA mode
- serve the dashboard at http://<board-ip>/
- keep the OhStem-style event_manager task scheduler
"""

import time
import os
import sys
from event_manager import *

import config


BUILD_NAME = "Yolo:Bit dashboard"
BUILD_DATE = "2026-05-13"


def _debug_boot():
    print("")
    print("=== {} boot {} ===".format(BUILD_NAME, BUILD_DATE))
    try:
        print("[Boot] sys.path:", sys.path)
    except Exception as e:
        print("[Boot] sys.path unavailable:", e)
    try:
        print("[Boot] files:", os.listdir())
    except Exception as e:
        print("[Boot] os.listdir failed:", e)
    print("[Boot] WIFI_SSID:", getattr(config, "WIFI_SSID", ""))
    print("[Boot] HTTP_PORT:", getattr(config, "HTTP_PORT", "missing"))
    print("[Boot] Task intervals wifi/dashboard:",
          getattr(config, "INTERVAL_TASK_WIFI_MS", "missing"),
          getattr(config, "INTERVAL_TASK_DASHBOARD_MS", "missing"))


_debug_boot()

try:
    import dashboard_state
    import task_wifi
    import task_dashboard
    print("[Boot] Dashboard modules imported")
except Exception as e:
    print("[Boot] Dashboard module import failed:", e)
    raise


event_manager.reset()
print("[Boot] event_manager reset")

dashboard_state.task_init()
task_wifi.task_init()
task_dashboard.task_init()
print("[Boot] task_init complete")

event_manager.add_timer_event(config.INTERVAL_TASK_WIFI_MS, task_wifi.task_run)
event_manager.add_timer_event(config.INTERVAL_TASK_DASHBOARD_MS, task_dashboard.task_run)
print("[Boot] timer events registered")

print("Yolo:Bit local dashboard starting.")

while True:
    event_manager.run()
    time.sleep_ms(10)
