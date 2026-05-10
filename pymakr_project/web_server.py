# Lightweight HTTP dashboard server for the YoloUno firmware.
# Hardware-specific behavior is provided by callbacks from main.py.

try:
    import ujson as json
except ImportError:
    import json

import gc
import socket


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>YoloUno Dashboard</title>
<style>
:root{font-family:Arial,sans-serif;color:#17202a;background:#f4f7f8}
body{margin:0;padding:18px}
main{max-width:860px;margin:0 auto}
h1{font-size:28px;margin:0 0 6px}
.muted{color:#59666f}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-top:18px}
.card{background:#fff;border:1px solid #dce4e8;border-radius:8px;padding:14px}
.label{font-size:12px;text-transform:uppercase;color:#61727d;letter-spacing:.04em}
.value{font-size:28px;font-weight:700;margin-top:8px}
.ok{color:#147a45}.bad{color:#b42318}
button{border:0;border-radius:6px;padding:11px 14px;margin:4px 6px 0 0;background:#1d4ed8;color:#fff;font-weight:700}
button.secondary{background:#475569}
pre{white-space:pre-wrap;background:#101828;color:#e5eef8;border-radius:8px;padding:12px;overflow:auto}
</style>
</head>
<body>
<main>
<h1>YoloUno Dashboard</h1>
<div class="muted">Served directly from the ESP32-S3 board</div>
<section class="grid">
<div class="card"><div class="label">Wi-Fi</div><div id="wifi" class="value">...</div></div>
<div class="card"><div class="label">IP</div><div id="ip" class="value">...</div></div>
<div class="card"><div class="label">Temperature</div><div id="temp" class="value">--</div></div>
<div class="card"><div class="label">Humidity</div><div id="humidity" class="value">--</div></div>
<div class="card"><div class="label">Relay</div><div id="relay" class="value">--</div>
<button onclick="setRelay(1)">On</button><button class="secondary" onclick="setRelay(0)">Off</button></div>
<div class="card"><div class="label">Button</div><div id="button" class="value">--</div></div>
</section>
<h2>Board status</h2>
<pre id="raw">Loading...</pre>
</main>
<script>
async function loadStatus(){
  try{
    const res=await fetch('/api/status');
    const data=await res.json();
    document.getElementById('wifi').textContent=data.wifi;
    document.getElementById('wifi').className='value '+(data.wifi==='connected'?'ok':'bad');
    document.getElementById('ip').textContent=data.ip||'--';
    document.getElementById('temp').textContent=data.temperature===null?'--':data.temperature+' C';
    document.getElementById('humidity').textContent=data.humidity===null?'--':data.humidity+' %';
    document.getElementById('relay').textContent=data.relay?'ON':'OFF';
    document.getElementById('button').textContent=data.button_pressed?'PRESSED':'idle';
    document.getElementById('raw').textContent=JSON.stringify(data,null,2);
  }catch(err){
    document.getElementById('raw').textContent='Dashboard request failed: '+err;
  }
}
async function setRelay(value){
  await fetch('/api/relay?value='+value,{method:'POST'});
  loadStatus();
}
loadStatus();
setInterval(loadStatus,2000);
</script>
</body>
</html>
"""


def query_value(query, key):
    for part in query.split("&"):
        if "=" not in part:
            continue
        name, value = part.split("=", 1)
        if name == key:
            return value
    return None


def bool_from_query(value):
    return value in ("1", "true", "on", "yes")


def send_response(client, status, content_type, body):
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


def handle_client(client, payload_status, set_relay, report_error):
    try:
        request = client.recv(1024)
        if not request:
            return
        first_line = request.decode().split("\r\n", 1)[0]
        parts = first_line.split(" ")
        if len(parts) < 2:
            send_response(client, "400 Bad Request", "text/plain", "Bad request")
            return

        method = parts[0]
        target = parts[1]
        path = target
        query = ""
        if "?" in target:
            path, query = target.split("?", 1)

        if method == "GET" and path == "/":
            send_response(client, "200 OK", "text/html", DASHBOARD_HTML)
        elif method == "GET" and path == "/api/status":
            send_response(client, "200 OK", "application/json", json.dumps(payload_status()))
        elif method == "GET" and path == "/api/scan":
            status = payload_status()
            body = {"i2c_devices": status.get("i2c_devices", [])}
            send_response(client, "200 OK", "application/json", json.dumps(body))
        elif method in ("GET", "POST") and path == "/api/relay":
            value = query_value(query, "value")
            if value is None:
                send_response(client, "400 Bad Request", "application/json", '{"error":"missing value"}')
                return
            set_relay(bool_from_query(value))
            send_response(client, "200 OK", "application/json", json.dumps(payload_status()))
        else:
            send_response(client, "404 Not Found", "text/plain", "Not found")
    except Exception as exc:
        report_error("HTTP handler failed: {}".format(exc))
    finally:
        try:
            client.close()
        except Exception:
            pass


def serve_forever(port, ip, payload_status, set_relay, report_error, lcd_write, on_idle):
    addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
    server = socket.socket()
    try:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except Exception:
        pass
    server.bind(addr)
    server.listen(3)
    server.settimeout(0.25)
    print("HTTP server listening on", addr)
    lcd_write("Server ready", ip[:16] if ip else "")

    while True:
        on_idle()
        try:
            client, _ = server.accept()
            handle_client(client, payload_status, set_relay, report_error)
        except OSError:
            pass
        gc.collect()
