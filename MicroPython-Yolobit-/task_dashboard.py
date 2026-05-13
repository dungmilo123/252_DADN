# -*- coding: utf-8 -*-
"""Polling HTTP dashboard task for Yolo:Bit."""

import gc

try:
    import ujson as json
except ImportError:
    import json

try:
    import usocket as socket
except ImportError:
    import socket

import config
import dashboard_state


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Yolo:Bit Dashboard</title>
<style>
:root{font-family:Verdana,serif;color:#1f2a24;background:#eef1e8}
body{margin:0;padding:16px}
main{max-width:760px;margin:0 auto}
h1{font-size:24px;margin:0 0 4px}
.muted{color:#617064;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:14px}
.card{background:#fff;border:1px solid #d8dfd2;border-radius:8px;padding:12px}
.label{font-size:11px;text-transform:uppercase;color:#647064}
.value{font-size:22px;font-weight:700;margin-top:6px;overflow-wrap:anywhere}
.ok{color:#126a40}.bad{color:#a83224}.warn{color:#9a5b00}
.controls{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
button{border:0;border-radius:6px;padding:10px 12px;background:#255f46;color:white;font-weight:700}
button.alt{background:#5c6b56}
pre{background:#17211a;color:#eaf3e5;border-radius:8px;padding:10px;white-space:pre-wrap;overflow:auto}
</style>
</head>
<body>
<main>
<h1>Yolo:Bit Dashboard</h1>
<div class="muted">Served directly from the board</div>
<section class="grid">
<div class="card"><div class="label">Wi-Fi</div><div id="wifi" class="value">...</div></div>
<div class="card"><div class="label">IP</div><div id="ip" class="value">...</div></div>
<div class="card"><div class="label">Uptime</div><div id="uptime" class="value">...</div></div>
<div class="card"><div class="label">Temperature</div><div id="temp" class="value">--</div></div>
<div class="card"><div class="label">Humidity</div><div id="hum" class="value">--</div></div>
<div class="card"><div class="label">Buttons</div><div id="buttons" class="value">--</div></div>
<div class="card"><div class="label">Display</div><div id="display" class="value">--</div></div>
<div class="card"><div class="label">DHT20</div><div id="dht" class="value">--</div></div>
</section>
<div class="controls">
<button onclick="setDisplay('heart')">Heart</button>
<button onclick="setDisplay('small_heart')">Small Heart</button>
<button class="alt" onclick="setDisplay('off')">Off</button>
<button class="alt" onclick="reconnectWifi()">Reconnect Wi-Fi</button>
</div>
<h2>Latest status</h2>
<pre id="raw">Loading...</pre>
</main>
<script>
function fmtMs(ms){var s=Math.floor(ms/1000);var m=Math.floor(s/60);var h=Math.floor(m/60);return h+'h '+(m%60)+'m '+(s%60)+'s'}
async function loadStatus(){
  try{
    const r=await fetch('/api/status');
    const d=await r.json();
    const wifi=document.getElementById('wifi');
    wifi.textContent=d.wifi;
    wifi.className='value '+(d.wifi==='connected'?'ok':(d.wifi==='connecting'?'warn':'bad'));
    document.getElementById('ip').textContent=d.ip||'--';
    document.getElementById('uptime').textContent=fmtMs(d.uptime_ms||0);
    document.getElementById('temp').textContent=d.temperature===null?'--':d.temperature+' C';
    document.getElementById('hum').textContent=d.humidity===null?'--':d.humidity+' %';
    document.getElementById('buttons').textContent='A '+(d.button_a?'down':'up')+' / B '+(d.button_b?'down':'up');
    document.getElementById('display').textContent=d.display_mode;
    document.getElementById('dht').textContent=d.dht20_present?'present':'missing';
    document.getElementById('raw').textContent=JSON.stringify(d,null,2);
    if(d.last_error){document.getElementById('raw').textContent+='\\n\\nError: '+d.last_error}
  }catch(e){
    document.getElementById('raw').textContent='Request failed: '+e;
  }
}
async function setDisplay(mode){await fetch('/api/display?mode='+mode,{method:'POST'});loadStatus()}
async function reconnectWifi(){await fetch('/api/system?reconnect_wifi=1',{method:'POST'});loadStatus()}
loadStatus();
setInterval(loadStatus,__STATUS_POLL_INTERVAL_MS__);
</script>
</body>
</html>
"""


_server = None
_server_ip = ""
_last_waiting_log_ms = 0


def task_init():
    print("[Dashboard] task_init")
    _close_server()


def task_run():
    global _last_waiting_log_ms
    dashboard_state.update_sensors(config.SENSOR_INTERVAL_MS)

    if dashboard_state.state["wifi"] != "connected":
        try:
            import time
            now = time.ticks_ms()
            if time.ticks_diff(now, _last_waiting_log_ms) >= 5000:
                _last_waiting_log_ms = now
                print("[Dashboard] waiting for Wi-Fi, state:", dashboard_state.state["wifi"])
        except Exception:
            pass
        _close_server()
        return

    _ensure_server()
    if _server is None:
        return

    try:
        client, _ = _server.accept()
    except OSError:
        return

    _handle_client(client)
    try:
        gc.collect()
    except Exception:
        pass


def _ensure_server():
    global _server, _server_ip
    ip = dashboard_state.state["ip"]
    if _server is not None and _server_ip == ip:
        return
    _close_server()
    try:
        addr = socket.getaddrinfo("0.0.0.0", config.HTTP_PORT)[0][-1]
        _server = socket.socket()
        try:
            _server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass
        _server.bind(addr)
        _server.listen(2)
        try:
            _server.settimeout(0)
        except Exception:
            pass
        try:
            _server.setblocking(False)
        except Exception:
            pass
        _server_ip = ip
        print("[Dashboard] HTTP listening on http://{}:{}/".format(ip, config.HTTP_PORT))
    except Exception as e:
        dashboard_state.set_error("HTTP server start failed: {}".format(e))
        _close_server()


def _close_server():
    global _server, _server_ip
    if _server is not None:
        try:
            _server.close()
        except Exception:
            pass
    _server = None
    _server_ip = ""


def _handle_client(client):
    try:
        try:
            client.settimeout(0.2)
        except Exception:
            pass
        request = client.recv(1024)
        if not request:
            return
        try:
            first_line = request.decode().split("\r\n", 1)[0]
        except Exception:
            _send(client, "400 Bad Request", "text/plain", "Bad request")
            return
        print("[HTTP]", first_line)

        parts = first_line.split(" ")
        if len(parts) < 2:
            _send(client, "400 Bad Request", "text/plain", "Bad request")
            return

        method = parts[0]
        target = parts[1]
        path, query = _split_target(target)

        if method == "GET" and path == "/":
            html = DASHBOARD_HTML.replace(
                "__STATUS_POLL_INTERVAL_MS__",
                str(config.STATUS_POLL_INTERVAL_MS),
            )
            _send(client, "200 OK", "text/html", html)
        elif method == "GET" and path == "/api/status":
            _send(client, "200 OK", "application/json", json.dumps(dashboard_state.snapshot()))
        elif method == "POST" and path == "/api/display":
            _handle_display(client, query)
        elif method == "POST" and path == "/api/system":
            _handle_system(client, query)
        else:
            _send(client, "404 Not Found", "text/plain", "Not found")
    except Exception as e:
        dashboard_state.set_error("HTTP request failed: {}".format(e))
    finally:
        try:
            client.close()
        except Exception:
            pass


def _handle_display(client, query):
    mode = _query_value(query, "mode")
    if mode is None or not dashboard_state.set_display_mode(mode):
        _send(client, "400 Bad Request", "application/json", '{"error":"invalid display mode"}')
        return
    _send(client, "200 OK", "application/json", json.dumps(dashboard_state.snapshot()))


def _handle_system(client, query):
    reconnect = _query_value(query, "reconnect_wifi")
    if reconnect != "1":
        _send(client, "400 Bad Request", "application/json", '{"error":"missing reconnect_wifi=1"}')
        return
    try:
        import task_wifi
        task_wifi.request_reconnect()
        dashboard_state.set_wifi("connecting", "")
        _send(client, "200 OK", "application/json", json.dumps(dashboard_state.snapshot()))
    except Exception as e:
        dashboard_state.set_error("Wi-Fi reconnect request failed: {}".format(e))
        _send(client, "500 Internal Server Error", "application/json", '{"error":"reconnect failed"}')


def _split_target(target):
    if "?" not in target:
        return target, ""
    return target.split("?", 1)


def _query_value(query, key):
    for part in query.split("&"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        if name == key:
            return value
    return None


def _send(client, status, content_type, body):
    if isinstance(body, str):
        body = body.encode()
    header = (
        "HTTP/1.0 {}\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n\r\n"
    ).format(status, content_type, len(body))
    client.send(header.encode())
    client.send(body)
