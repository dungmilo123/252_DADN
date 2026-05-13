# AIOT KIT (OhStem) – lib/aiot

Các module tương ứng **Mở rộng → AIOT KIT** trên app.ohstem.vn.

**Nguồn:** [AITT-VN/yolobit_extension_aiot](https://github.com/AITT-VN/yolobit_extension_aiot)

Cần Yolo:Bit có **yolobit** (pin19, pin20, …) và mạch mở rộng tương thích.

---

## aiot_dht20 – Cảm biến nhiệt độ, độ ẩm DHT20

**Import:** `from lib.aiot.aiot_dht20 import DHT20`

| Hàm | Mô tả |
|-----|--------|
| `DHT20()` | Khởi tạo. I2C: SCL = pin19, SDA = pin20 (yolobit). |
| `dht.read_dht20()` | Đọc dữ liệu thô, trả về list 7 byte. |
| `dht.dht20_temperature()` | Trả về nhiệt độ (°C), 1 chữ số thập phân. |
| `dht.dht20_humidity()` | Trả về độ ẩm (%), 1 chữ số thập phân. |

**Ví dụ:**

```python
from lib.aiot.aiot_dht20 import DHT20
dht = DHT20()
print(dht.dht20_temperature(), dht.dht20_humidity())
```

---

## aiot_rgbled – LED RGB (NeoPixel)

**Import:** `from lib.aiot.aiot_rgbled import RGBLed`

| Hàm | Mô tả |
|-----|--------|
| `RGBLed(pin, num_leds)` | Khởi tạo. `pin`: số chân GPIO (vd `pin14.pin` từ yolobit). `num_leds`: số LED (vd 4). |
| `rgb.show(index, color, delay=None)` | Hiển thị màu. `index`: 0 = tất cả LED, 1..num_leds = từng LED. `color`: tuple `(r, g, b)` (0–255). `delay`: nếu có, sau đó tắt (0,0,0). |
| `rgb.off(index)` | Tắt: `index` 0 = tất cả, 1..num_leds = từng LED. |

**Ví dụ:**

```python
from yolobit import *
from lib.aiot.aiot_rgbled import RGBLed
rgb = RGBLed(pin14.pin, 4)
rgb.show(1, (255, 0, 0))   # LED 1 đỏ
rgb.show(0, (0, 255, 0))   # tất cả xanh lá
rgb.off(0)
```
