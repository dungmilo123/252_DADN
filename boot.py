# -*- coding: utf-8 -*-
# boot.py - Chạy trước main.py trên thiết bị (tùy chọn).
# Có thể dùng để cấu hình UART, WiFi, ... Nếu không cần thì để trống hoặc gọi main.

# Ví dụ: bật UART cho Serial Monitor (thường đã mặc định)
# import machine
# uart = machine.UART(0, baudrate=115200)