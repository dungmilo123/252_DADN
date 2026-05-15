# Thư mục lib – Thư viện OhStem cho VSCode/MicroPython

Các thư viện trong thư mục này tương đương **Mở rộng** trên app.ohstem.vn (AIOT KIT, Sự kiện, MQTT, NTP). Khi **Sync project to device**, PyMakr đồng bộ cả cây thư mục nên **lib/** (và **lib/aiot/**) được upload lên Yolo:Bit; dùng **sync_file_types = "py"** thì chỉ file .py được sync (README không đưa lên).

**Import (sau khi Sync, trên board):**

```python
from lib.mqtt import mqtt
from lib.ntp_helper import set_time_from_ntp, get_time, get_time_str
from lib.event_manager_ohstem import event_manager
from lib.aiot.aiot_dht20 import DHT20
from lib.aiot.aiot_rgbled import RGBLed
```

---

## 1. MQTT (OhStem)

**Nguồn:** [AITT-VN/yolobit_extension_mqtt](https://github.com/AITT-VN/yolobit_extension_mqtt)

**File:** `mqtt.py`, `umqtt_simple.py`, `umqtt_robust.py`, `utility.py`

### API – đối tượng `mqtt`

| Hàm / thuộc tính | Mô tả |
|------------------|--------|
| `mqtt.connect_wifi(ssid, password, wait_for_connected=True)` | Kết nối WiFi. `wait_for_connected`: chờ tới khi kết nối xong (mặc định True). |
| `mqtt.wifi_connected()` | Trả về `True`/`False` — WiFi đã kết nối chưa. |
| `mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='', password='')` | Kết nối broker MQTT. Với `mqtt.ohstem.vn` hoặc `io.adafruit.com`, topic có prefix `username/feeds/`. |
| `mqtt.publish(topic, message)` | Gửi tin lên topic. Giới hạn tối thiểu 1 giây giữa hai lần gửi. |
| `mqtt.on_receive_message(topic, callback)` | Đăng ký callback khi nhận tin trên topic. `callback(msg)` nhận chuỗi `msg`. |
| `mqtt.check_message()` | Kiểm tra tin đến; gọi trong vòng lặp chính. Tự reconnect WiFi nếu mất kết nối. |

### Ví dụ

```python
from lib.mqtt import mqtt
mqtt.connect_wifi('TenWiFi', 'MatKhau')
mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='user', password='')
mqtt.publish('V1', 'Hello')
def on_msg(msg):
    print('Nhan:', msg)
mqtt.on_receive_message('V2', on_msg)
while True:
    mqtt.check_message()
    time.sleep_ms(10)
```

---

## 2. NTP – Lấy thời gian theo internet

**Nguồn block NTP:** [AITT-VN/yolobit_ntp](https://github.com/AITT-VN/yolobit_ntp)  
*File `ntp_helper.py` trong project dùng `ntptime` + `machine.RTC` tương thích block.*

**File:** `ntp_helper.py`

### API

| Hàm | Mô tả |
|-----|--------|
| `set_time_from_ntp(gmt_offset=7)` | Đồng bộ giờ từ NTP, áp múi giờ. Gọi **sau khi đã kết nối WiFi**. Trả về `True`/`False`. |
| `get_time()` | Trả về `(year, month, day, hour, minute, second)` từ RTC. |
| `get_time_str()` | Trả về chuỗi `"YYYY-MM-DD HH:MM:SS"`. |

### Ví dụ

```python
from lib.mqtt import mqtt
from lib.ntp_helper import set_time_from_ntp, get_time, get_time_str
mqtt.connect_wifi('TenWiFi', 'MatKhau')
set_time_from_ntp(7)
print(get_time_str())
y, mo, d, h, mi, s = get_time()
```

---

## 3. Sự kiện (event_manager đầy đủ OhStem)

**Nguồn:** [AITT-VN/yolobit_extension_events](https://github.com/AITT-VN/yolobit_extension_events)

**File:** `event_manager_ohstem.py`

### API – đối tượng `event_manager`

| Hàm | Mô tả |
|-----|--------|
| `event_manager.reset()` | Xóa toàn bộ sự kiện đã đăng ký. |
| `event_manager.add_timer_event(interval, callback)` | Sự kiện định thời. `interval`: chu kỳ (ms). `callback`: hàm không tham số. |
| `event_manager.add_message_event(message_index, callback)` | Sự kiện theo “message”. Khi gọi `broadcast_message(message_index)` thì gọi `callback()`. |
| `event_manager.add_condition_event(condition, callback)` | Sự kiện theo điều kiện. `condition()` trả về True/False; khi True gọi `callback()` (có thể trong thread). |
| `event_manager.broadcast_message(message_index)` | Kích hoạt mọi callback đăng ký với `message_index`. |
| `event_manager.run()` | Chạy kiểm tra timer/condition và gọi callback. Gọi trong vòng lặp chính. |

### Ví dụ

```python
from lib.event_manager_ohstem import event_manager
import time
event_manager.reset()
event_manager.add_timer_event(1000, lambda: print('timer'))
def on_msg():
    print('message 0')
event_manager.add_message_event(0, on_msg)
event_manager.broadcast_message(0)
while True:
    event_manager.run()
    time.sleep_ms(10)
```

---

## 4. AIOT KIT

**Nguồn:** [AITT-VN/yolobit_extension_aiot](https://github.com/AITT-VN/yolobit_extension_aiot)

Cần Yolo:Bit có **yolobit** và mạch mở rộng tương thích.

### 4.1. DHT20 – Cảm biến nhiệt độ, độ ẩm

**File:** `aiot/aiot_dht20.py`

| Hàm | Mô tả |
|-----|--------|
| `DHT20()` | Khởi tạo, I2C qua pin19 (SCL), pin20 (SDA). |
| `dht.read_dht20()` | Đọc dữ liệu thô (list 7 byte). |
| `dht.dht20_temperature()` | Nhiệt độ (°C). |
| `dht.dht20_humidity()` | Độ ẩm (%). |

### 4.2. RGBLed – LED RGB (NeoPixel)

**File:** `aiot/aiot_rgbled.py`

| Hàm | Mô tả |
|-----|--------|
| `RGBLed(pin, num_leds)` | Khởi tạo. `pin`: GPIO. `num_leds`: số LED (vd 4). |
| `rgb.show(index, color, delay=None)` | Hiển thị màu. `index`: 0 = tất cả, 1..num_leds = từng LED. `color`: `(r, g, b)` 0–255. |
| `rgb.off(index)` | Tắt LED. |

Chi tiết thêm: **`aiot/README.md`**.

---

## Link nguồn OhStem (GitHub AITT-VN)

| Thư viện | Repository |
|----------|------------|
| MQTT | https://github.com/AITT-VN/yolobit_extension_mqtt |
| Sự kiện | https://github.com/AITT-VN/yolobit_extension_events |
| NTP (block) | https://github.com/AITT-VN/yolobit_ntp |
| AIOT KIT | https://github.com/AITT-VN/yolobit_extension_aiot |

Tổ chức: https://github.com/AITT-VN
