# -*- coding: utf-8 -*-
"""Wi-Fi station connection task for the board-hosted dashboard."""

import time
import network

import config
import dashboard_state


_wlan = None
_connect_started_ms = 0
_failed_at_ms = 0
_last_connected_ip = ""
_reconnect_requested = False
_last_debug_ms = 0


def _ticks_ms():
    return time.ticks_ms()


def _ticks_diff(new, old):
    return time.ticks_diff(new, old)


def task_init():
    global _wlan
    print("[WiFi] task_init")
    _wlan = network.WLAN(network.STA_IF)
    try:
        print("[WiFi] initial active:", _wlan.active(), "connected:", _wlan.isconnected())
    except Exception as e:
        print("[WiFi] initial status unavailable:", e)
    _begin_connect(force=True)


def force_reconnect():
    global _reconnect_requested
    print("[WiFi] reconnect requested")
    _reconnect_requested = True


def request_reconnect():
    force_reconnect()


def _run_requested_reconnect():
    global _reconnect_requested
    if not _reconnect_requested:
        return False
    _reconnect_requested = False
    _begin_connect(force=True)
    return True


def is_connected():
    return _wlan is not None and _wlan.isconnected()


def ip_address():
    if not is_connected():
        return ""
    try:
        return _wlan.ifconfig()[0]
    except Exception:
        return ""


def _begin_connect(force=False):
    global _connect_started_ms, _failed_at_ms, _last_connected_ip

    ssid = getattr(config, "WIFI_SSID", "")
    password = getattr(config, "WIFI_PASSWORD", "")
    _connect_started_ms = _ticks_ms()
    _failed_at_ms = 0
    _last_connected_ip = ""

    if not ssid:
        dashboard_state.set_wifi("failed", "")
        dashboard_state.set_error("WIFI_SSID is empty in config.py")
        dashboard_state.show_wifi_failed()
        _failed_at_ms = _ticks_ms()
        return

    try:
        print("[WiFi] begin_connect force:", force,
              "ssid:", ssid,
              "password_len:", len(password))
        if force and _wlan.active():
            try:
                _wlan.disconnect()
            except Exception:
                pass
        if not _wlan.active():
            _wlan.active(True)
        dashboard_state.set_wifi("connecting", "")
        dashboard_state.show_wifi_connecting()
        print("[WiFi] Connecting to:", ssid)
        _wlan.connect(ssid, password)
    except Exception as e:
        dashboard_state.set_wifi("failed", "")
        dashboard_state.set_error("Wi-Fi connect start failed: {}".format(e))
        dashboard_state.show_wifi_failed()
        _failed_at_ms = _ticks_ms()


def _mark_failed(message):
    global _failed_at_ms
    dashboard_state.set_wifi("failed", "")
    dashboard_state.set_error(message)
    dashboard_state.show_wifi_failed()
    _failed_at_ms = _ticks_ms()
    print("[WiFi]", message)


def task_run():
    global _last_connected_ip, _last_debug_ms

    if _wlan is None:
        return

    if _run_requested_reconnect():
        return

    wifi_state = dashboard_state.state["wifi"]
    now = _ticks_ms()

    if _ticks_diff(now, _last_debug_ms) >= 5000:
        _last_debug_ms = now
        try:
            print("[WiFi] tick state:", wifi_state,
                  "active:", _wlan.active(),
                  "connected:", _wlan.isconnected(),
                  "status:", _wlan.status())
        except Exception as e:
            print("[WiFi] tick state:", wifi_state, "status read failed:", e)

    if _wlan.isconnected():
        ip = ip_address()
        if wifi_state != "connected" or ip != _last_connected_ip:
            _last_connected_ip = ip
            dashboard_state.set_wifi("connected", ip)
            dashboard_state.clear_error()
            print("[WiFi] Connected. IP:", ip)
            dashboard_state.show_ip(ip)
        return

    if wifi_state == "connected":
        _mark_failed("Wi-Fi disconnected")
        return

    if wifi_state == "connecting":
        dashboard_state.show_wifi_connecting()
        if _ticks_diff(now, _connect_started_ms) >= config.WIFI_CONNECT_TIMEOUT_MS:
            _mark_failed("Wi-Fi connection timed out")
        return

    if wifi_state == "failed":
        if _failed_at_ms == 0:
            _mark_failed("Wi-Fi connection failed")
            return
        if _ticks_diff(now, _failed_at_ms) >= config.WIFI_RETRY_DELAY_MS:
            _begin_connect(force=True)
