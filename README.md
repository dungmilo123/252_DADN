# YoloUno ESP32-S3 Wi-Fi Dashboard

This project contains MicroPython firmware for a YoloUno / ESP32-S3 board.
After boot, the board joins a configured Wi-Fi network and serves a small web
dashboard directly from the board.

## What It Does

- Connects the board to Wi-Fi in station mode.
- Runs an HTTP server on the board at `http://<board-ip>/`.
- Shows board status, relay state, optional DHT20 readings, optional LCD state,
  and I2C scan results.
- Lets the dashboard turn the relay on and off.
- Uses the onboard LED as the primary status/error indicator.
- Uses the LCD only when it is connected and detected.

## Files

- `main.py`: board firmware and web server.
- `wifi_config.py`: Wi-Fi SSID/password configuration.
- `lcd_i2c.py`: HD44780 16x2 LCD driver over PCF8574 I2C.
- `main_rtos.py`: older Lab 2 GPIO/I2C example kept for reference.
- `main_lab3.py`: older Lab 3 note kept for reference.
- `pymakr_project/`: upload-ready copy for opening directly with Pymakr.

## Configure Wi-Fi

Edit `wifi_config.py` before uploading:

```python
WIFI_SSID = "your_wifi_name"
WIFI_PASSWORD = "your_wifi_password"
```

If `WIFI_SSID` is empty or the network cannot be joined, the board keeps
retrying and reports the error through the onboard LED. If an LCD is attached,
it also shows the Wi-Fi failure there.

## Upload With Pymakr

1. Install VS Code and the Pymakr extension.
2. Open either this folder or `pymakr_project/`.
3. Connect the YoloUno board by USB.
4. Set `wifi_config.py`.
5. Use Pymakr to upload/sync the Python files to the board.
6. Reset the board.

After a successful Wi-Fi connection, the board prints its IP address in the
REPL. If an LCD is attached, it shows the IP there too. Open the dashboard:

```text
http://<board-ip>/
```

The browser device must be on the same Wi-Fi network as the board. Some school
or office Wi-Fi networks block device-to-device traffic; if the board connects
but the dashboard cannot be opened, check for client isolation on the router.

## LED Status

- Fast blinking during Wi-Fi connection.
- Three short blinks repeated when Wi-Fi fails and the board is waiting to retry.
- Solid on briefly after Wi-Fi connects.
- Short heartbeat blink while the HTTP server is running.

The LED is intentionally reserved for board status and errors. The dashboard
controls the relay, not the status LED.

## HTTP Endpoints

- `GET /`: dashboard HTML.
- `GET /api/status`: JSON board status.
- `GET /api/scan`: I2C scan result.
- `POST /api/relay?value=1`: relay on.
- `POST /api/relay?value=0`: relay off.

Example status response:

```json
{
  "wifi": "connected",
  "ip": "192.168.1.42",
  "relay": false,
  "temperature": 27.4,
  "humidity": 63.1,
  "lcd": true,
  "dht20": true,
  "last_error": null
}
```

## Hardware Pins

- Onboard/status LED: GPIO48.
- Button input: GPIO2.
- Relay output: GPIO5.
- Grove I2C SDA: GPIO11.
- Grove I2C SCL: GPIO12.

Adjust these constants in `main.py` if your board wiring differs.
