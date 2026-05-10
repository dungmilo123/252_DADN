# HD44780 16x2 over I2C PCF8574 backpack (MicroPython)
# ASCII only; 4-space indents throughout.

import time


class I2cLcd:
    def __init__(self, i2c, addr=0x27, cols=16, rows=2):
        self.i2c = i2c
        self.addr = addr
        self.cols = cols
        self.rows = rows
        self.backlight = 0x08
        self._init_lcd()

    def _write(self, data):
        self.i2c.writeto(self.addr, bytes([data | self.backlight]))

    def _pulse(self, data):
        e_high = data | 0x04
        e_low = data & 0xFB
        self._write(e_high)
        time.sleep_us(1)
        self._write(e_low)
        time.sleep_us(50)

    def _send_nibble(self, nibble, rs=0):
        data = (nibble & 0xF0) | (0x01 if rs else 0x00)
        self._write(data)
        self._pulse(data)

    def _send_byte(self, value, rs=0):
        self._send_nibble(value & 0xF0, rs)
        self._send_nibble((value << 4) & 0xF0, rs)

    def _cmd(self, cmd):
        self._send_byte(cmd, rs=0)
        time.sleep_ms(2)

    def _data(self, val):
        self._send_byte(val, rs=1)

    def _init_lcd(self):
        time.sleep_ms(50)
        for _ in range(3):
            self._send_nibble(0x30, rs=0)
            time.sleep_ms(5)
        self._send_nibble(0x20, rs=0)
        time.sleep_ms(5)
        self._cmd(0x28)
        self._cmd(0x0C)
        self._cmd(0x06)
        self.clear()

    def clear(self):
        self._cmd(0x01)
        time.sleep_ms(2)

    def move_to(self, col, row):
        row_offsets = (0x00, 0x40, 0x14, 0x54)
        self._cmd(0x80 | (col + row_offsets[row]))

    def putstr(self, s):
        for ch in s:
            self._data(ord(ch))

    def write_line(self, row, text):
        # MicroPython on some boards has no str.ljust; pad manually.
        s = text if text else ""
        if len(s) > self.cols:
            s = s[: self.cols]
        pad = self.cols - len(s)
        if pad:
            s = s + (" " * pad)
        self.move_to(0, row)
        self.putstr(s)
