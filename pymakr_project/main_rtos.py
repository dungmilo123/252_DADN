# LAB 2: GPIO and I2C Peripherals (Yolo UNO / ESP32-S3 MicroPython)
#
# Grove I2C (I2C1..I2C4 share one bus): SDA=GPIO11, SCL=GPIO12.
# Wiring: I2C1 Grove -> DHT20, I2C2 Grove -> LCD (parallel bus; addresses differ).
#
# Features:
# - GPIO: button controls LED + relay
# - I2C: read DHT20 and show temperature/humidity on LCD 16x2 (PCF8574)
#
# NOTE: Relay must not use GPIO12 (SCL). Adjust GPIO constants if your kit differs.

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
from machine import I2C, Pin

from lcd_i2c import I2cLcd


async def asleep_ms(ms):
    if hasattr(asyncio, "sleep_ms"):
        await asyncio.sleep_ms(ms)
    else:
        await asyncio.sleep(ms / 1000)


def create_task(coro):
    return asyncio.create_task(coro)


# -----------------------
# Pin mapping
# -----------------------
BUTTON_PIN_GPIO = 2  # A1 on header; or use BOOT GPIO0 if wired on board
LED_PIN_GPIO = 48    # D13 on Yolo UNO pinout
RELAY_PIN_GPIO = 5   # D2 - not GPIO12 (SCL for Grove I2C)

# Yolo UNO Grove I2C1..I2C4: same SDA/SCL
I2C_SDA_GPIO = 11
I2C_SCL_GPIO = 12


# -----------------------
# Simple DHT20 driver
# -----------------------
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
        time.sleep_ms(90)
        for _ in range(10):
            if not self._is_busy():
                break
            time.sleep_ms(10)

        data = self.i2c.readfrom(self.address, 7)
        raw_h = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        raw_t = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        humidity = (raw_h * 100.0) / 1048576.0
        temperature = (raw_t * 200.0) / 1048576.0 - 50.0
        return temperature, humidity


# -----------------------
# Hardware init
# -----------------------
button = Pin(BUTTON_PIN_GPIO, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN_GPIO, Pin.OUT)
relay = Pin(RELAY_PIN_GPIO, Pin.OUT)

i2c = I2C(0, scl=Pin(I2C_SCL_GPIO), sda=Pin(I2C_SDA_GPIO), freq=100000)
dht20 = None
lcd = None


def set_outputs(on):
    value = 1 if on else 0
    led.value(value)
    relay.value(value)


def init_i2c_devices():
    global dht20, lcd
    devices = i2c.scan()
    print("I2C scan:", [hex(x) for x in devices])
    if DHT20.ADDRESS in devices:
        dht20 = DHT20(i2c)
    else:
        print("Warning: DHT20 not found on I2C.")
    # PCF8574 LCD backpack: jumpers set A2..A0 -> common addrs 0x20-0x27; some modules use 0x3F.
    # Yolo UNO + Grove LCD often shows up as 0x21 (not only 0x27).
    lcd_candidates = (0x27, 0x3F, 0x21, 0x20, 0x22, 0x23, 0x24, 0x25, 0x26)
    lcd = None
    for addr in lcd_candidates:
        if addr not in devices or addr == DHT20.ADDRESS:
            continue
        try:
            lcd = I2cLcd(i2c, addr=addr, cols=16, rows=2)
            print("LCD OK at", hex(addr))
            break
        except Exception as exc:
            print("LCD init failed at", hex(addr), ":", exc)
            lcd = None
    if lcd is None:
        print("Warning: LCD (PCF8574) not found or init failed on I2C.")


# -----------------------
# Tasks
# -----------------------
async def task_gpio_button_control():
    state = False
    last_pressed = 1
    set_outputs(state)
    while True:
        pressed = button.value()  # pull-up: 0 means pressed
        if last_pressed == 1 and pressed == 0:
            state = not state
            set_outputs(state)
            print("GPIO state:", "ON" if state else "OFF")
            await asleep_ms(180)  # debounce
        last_pressed = pressed
        await asleep_ms(30)


async def task_i2c_dht20_lcd():
    if lcd:
        lcd.write_line(0, "Lab2 I2C ready")
        lcd.write_line(1, "Init DHT20...")

    while True:
        if dht20:
            try:
                t, h = dht20.read()
                line1 = "Temp:{:5.1f}C".format(t)
                line2 = "Humi:{:5.1f}%".format(h)
                print(line1, line2)
                if lcd:
                    lcd.write_line(0, line1)
                    lcd.write_line(1, line2)
            except Exception as exc:
                print("DHT20 read error:", exc)
                if lcd:
                    lcd.write_line(0, "DHT20 read error")
                    lcd.write_line(1, "Check wiring")
        else:
            if lcd:
                lcd.write_line(0, "DHT20 not found")
                lcd.write_line(1, "Check wiring")
        await asleep_ms(2000)


async def main():
    print("LAB2 started")
    init_i2c_devices()
    create_task(task_gpio_button_control())
    create_task(task_i2c_dht20_lcd())
    while True:
        await asleep_ms(200)


try:
    asyncio.run(main())
except Exception:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
