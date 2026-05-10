# YoloUno ESP32-S3 MicroPython dashboard firmware.
# The board connects to a configured Wi-Fi network and serves a small
# dashboard from the board itself at http://<board-ip>/.

import gc
import network
import time
from machine import I2C, Pin

from web_server import serve_forever

try:
    from lcd_i2c import I2cLcd
except Exception:
    I2cLcd = None

try:
    from wifi_config import WIFI_PASSWORD, WIFI_SSID
except Exception:
    WIFI_SSID = ""
    WIFI_PASSWORD = ""


LED_PIN_GPIO = 48
BUTTON_PIN_GPIO = 2
RELAY_PIN_GPIO = 5

I2C_SDA_GPIO = 11
I2C_SCL_GPIO = 12
I2C_FREQ = 100000

WIFI_CONNECT_TIMEOUT_MS = 15000
WIFI_RETRY_DELAY_MS = 30000
HTTP_PORT = 80


def ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def ticks_diff(new, old):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(new, old)
    return new - old


def sleep_ms(ms):
    if hasattr(time, "sleep_ms"):
        time.sleep_ms(ms)
    else:
        time.sleep(ms / 1000)


class DHT20:
    ADDRESS = 0x38

    def __init__(self, i2c, address=ADDRESS):
        self.i2c = i2c
        self.address = address

    def _trigger_measure(self):
        self.i2c.writeto(self.address, b"\xAC\x33\x00")

    def _is_busy(self):
        status = self.i2c.readfrom(self.address, 1)[0]
        return (status & 0x80) != 0

    def read(self):
        self._trigger_measure()
        sleep_ms(90)
        for _ in range(10):
            if not self._is_busy():
                break
            sleep_ms(10)

        data = self.i2c.readfrom(self.address, 7)
        raw_h = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        humidity = (raw_h * 100.0) / 1048576.0
        temperature = (raw_t * 200.0) / 1048576.0 - 50.0
        return temperature, humidity


status_led = Pin(LED_PIN_GPIO, Pin.OUT)
button = Pin(BUTTON_PIN_GPIO, Pin.IN, Pin.PULL_UP)
relay = Pin(RELAY_PIN_GPIO, Pin.OUT)
relay.value(0)

i2c = None
lcd = None
dht20 = None
i2c_devices = []

state = {
    "boot_ms": ticks_ms(),
    "wifi": "starting",
    "ip": None,
    "ssid": WIFI_SSID,
    "lcd": False,
    "dht20": False,
    "relay": False,
    "button_pressed": False,
    "temperature": None,
    "humidity": None,
    "last_error": None,
    "last_sensor_ms": 0,
}


def set_error(message):
    state["last_error"] = message
    print("ERROR:", message)


def led(value):
    status_led.value(1 if value else 0)


def blink_pattern(count, on_ms=120, off_ms=140, pause_ms=900):
    for _ in range(count):
        led(True)
        sleep_ms(on_ms)
        led(False)
        sleep_ms(off_ms)
    sleep_ms(pause_ms)


def led_connecting_tick(last_toggle):
    now = ticks_ms()
    if ticks_diff(now, last_toggle) >= 120:
        status_led.value(0 if status_led.value() else 1)
        return now
    return last_toggle


def heartbeat_tick(last_heartbeat):
    now = ticks_ms()
    if ticks_diff(now, last_heartbeat) >= 4000:
        led(True)
        sleep_ms(35)
        led(False)
        return now
    return last_heartbeat


def lcd_write(line1, line2=""):
    if not lcd:
        return
    try:
        lcd.write_line(0, line1)
        lcd.write_line(1, line2)
    except Exception as exc:
        state["lcd"] = False
        set_error("LCD write failed: {}".format(exc))


def init_i2c_devices():
    global dht20, i2c, i2c_devices, lcd

    try:
        i2c = I2C(0, scl=Pin(I2C_SCL_GPIO), sda=Pin(I2C_SDA_GPIO), freq=I2C_FREQ)
        i2c_devices = i2c.scan()
        print("I2C scan:", [hex(x) for x in i2c_devices])
    except Exception as exc:
        i2c = None
        i2c_devices = []
        set_error("I2C init failed: {}".format(exc))
        return

    if DHT20.ADDRESS in i2c_devices:
        dht20 = DHT20(i2c)
        state["dht20"] = True
    else:
        print("DHT20 not found")

    if I2cLcd is None:
        print("LCD driver not available")
        return

    lcd_candidates = (0x27, 0x3F, 0x21, 0x20, 0x22, 0x23, 0x24, 0x25, 0x26)
    for addr in lcd_candidates:
        if addr not in i2c_devices or addr == DHT20.ADDRESS:
            continue
        try:
            lcd = I2cLcd(i2c, addr=addr, cols=16, rows=2)
            state["lcd"] = True
            print("LCD OK at", hex(addr))
            return
        except Exception as exc:
            set_error("LCD init failed at {}: {}".format(hex(addr), exc))
            lcd = None
            state["lcd"] = False
    print("LCD not found")


def connect_wifi_once():
    if not WIFI_SSID:
        set_error("Missing WIFI_SSID in wifi_config.py")
        return None

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        state["wifi"] = "connected"
        state["ip"] = ip
        return ip

    state["wifi"] = "connecting"
    print("Connecting to Wi-Fi:", WIFI_SSID)
    lcd_write("Connecting WiFi", WIFI_SSID[:16])
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    start = ticks_ms()
    last_toggle = ticks_ms()
    while not wlan.isconnected():
        last_toggle = led_connecting_tick(last_toggle)
        if ticks_diff(ticks_ms(), start) > WIFI_CONNECT_TIMEOUT_MS:
            state["wifi"] = "failed"
            set_error("Wi-Fi connection failed")
            return None
        sleep_ms(20)

    ip = wlan.ifconfig()[0]
    state["wifi"] = "connected"
    state["ip"] = ip
    state["last_error"] = None
    led(True)
    sleep_ms(1200)
    led(False)
    print("Wi-Fi connected:", ip)
    lcd_write("WiFi OK", ip[:16])
    return ip


def connect_wifi_with_retry():
    while True:
        ip = connect_wifi_once()
        if ip:
            return ip

        lcd_write("WiFi failed", "Retrying...")
        print("Wi-Fi retry in {} ms".format(WIFI_RETRY_DELAY_MS))
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < WIFI_RETRY_DELAY_MS:
            blink_pattern(3)


def read_sensors(force=False):
    now = ticks_ms()
    if not force and ticks_diff(now, state["last_sensor_ms"]) < 2000:
        return
    state["last_sensor_ms"] = now
    state["button_pressed"] = button.value() == 0

    if not dht20:
        return

    try:
        temperature, humidity = dht20.read()
        state["temperature"] = round(temperature, 1)
        state["humidity"] = round(humidity, 1)
    except Exception as exc:
        state["temperature"] = None
        state["humidity"] = None
        set_error("DHT20 read failed: {}".format(exc))


def set_relay(value):
    state["relay"] = bool(value)
    relay.value(1 if state["relay"] else 0)


def payload_status():
    read_sensors()
    return {
        "wifi": state["wifi"],
        "ip": state["ip"],
        "ssid": state["ssid"],
        "uptime_ms": ticks_diff(ticks_ms(), state["boot_ms"]),
        "lcd": state["lcd"],
        "dht20": state["dht20"],
        "relay": state["relay"],
        "button_pressed": state["button_pressed"],
        "temperature": state["temperature"],
        "humidity": state["humidity"],
        "i2c_devices": [hex(x) for x in i2c_devices],
        "last_error": state["last_error"],
        "free_memory": gc.mem_free() if hasattr(gc, "mem_free") else None,
    }


server_heartbeat_ms = [ticks_ms()]


def server_idle():
    server_heartbeat_ms[0] = heartbeat_tick(server_heartbeat_ms[0])


def main():
    print("YoloUno Wi-Fi dashboard booting")
    led(False)
    init_i2c_devices()
    connect_wifi_with_retry()
    read_sensors(force=True)
    serve_forever(
        HTTP_PORT,
        state["ip"],
        payload_status,
        set_relay,
        set_error,
        lcd_write,
        server_idle,
    )


main()
