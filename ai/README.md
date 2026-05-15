# Tiny Neural Network trên Yolo:Bit — Hướng dẫn cho sinh viên

## Tổng quan

Bài này hướng dẫn bạn **train một mạng neuron nhỏ (Tiny NN)** trên PC rồi **deploy lên Yolo:Bit (MicroPython)** để phân loại môi trường dựa trên **nhiệt độ** và **độ ẩm** từ cảm biến **DHT20**.

### Bài toán

- **Input**: 2 giá trị từ DHT20: nhiệt độ (°C) và độ ẩm (%).
- **Output**: 1 trong 3 nhãn (labels):
  - `binh_thuong` — môi trường bình thường
  - `nong_am` — nóng và ẩm (cảnh báo)
  - `lanh_kho` — lạnh và khô (cảnh báo)
- **Model**: Tiny Neural Network 3 layer (2 → 8 → 4 → 3), tổng 75 tham số.

### Luồng hoạt động tổng thể

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PC (Python + PyTorch)                          │
│                                                                             │
│  Bước 1: Thu thập data ──→ CSV (temp, humidity, label)                      │
│  Bước 2: Train model   ──→ best_model.pth + train_config.json              │
│  Bước 3: Export model   ──→ model.py (weights dạng list Python)             │
│                                                                             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │  Sync (PyMakr)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Yolo:Bit (MicroPython)                              │
│                                                                             │
│  Bước 4: inference.py đọc model.py                                          │
│          DHT20 → (temp, hum) → normalize → forward pass → label            │
│                                                                             │
│  KHÔNG train trên board. Board chỉ chạy inference (dự đoán).               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Kiến trúc model

```
       Input (2)            Hidden Layer 1 (8)       Hidden Layer 2 (4)       Output (3)
    ┌──────────┐           ┌────────────────┐       ┌────────────────┐      ┌─────────────┐
    │   temp   ─┼──×W1──→  │ 8 neuron, ReLU │──×W2→ │ 4 neuron, ReLU │──×W3→│ 3 scores    │
    │ humidity ─┼──×W1──→  │                │       │                │      │ → argmax    │
    └──────────┘           └────────────────┘       └────────────────┘      │ → label     │
                                                                            └─────────────┘
```

### Tham số

| Layer | Kích thước | Weights | Biases | Tổng |
|-------|-----------|---------|--------|------|
| Layer 1 (input → hidden1) | 2 × 8 | 16 | 8 | 24 |
| Layer 2 (hidden1 → hidden2) | 8 × 4 | 32 | 4 | 36 |
| Layer 3 (hidden2 → output) | 4 × 3 | 12 | 3 | 15 |
| **Tổng** | | **60** | **15** | **75** |

### Forward pass (mỗi lần predict)

```
1. Normalize:  x = [(temp - mean) / std, (humidity - mean) / std]
2. Layer 1:    h1 = ReLU(x @ W1 + b1)         # 2→8, 16 phép nhân + 8 cộng
3. Layer 2:    h2 = ReLU(h1 @ W2 + b2)        # 8→4, 32 phép nhân + 4 cộng
4. Layer 3:    scores = h2 @ W3 + b3           # 4→3, 12 phép nhân + 3 cộng
5. Output:     class = argmax(scores)          # chọn score cao nhất
```

Tổng cộng: **60 phép nhân + 15 phép cộng** mỗi lần predict. Thời gian < 1ms trên ESP32.

---

## Yêu cầu

### Trên PC (train model)

- Python 3.8+
- Cài thư viện:
  ```bash
  cd ai
  pip install -r requirements.txt
  ```

### Trên Yolo:Bit

- Firmware MicroPython OhStem
- Cảm biến DHT20 (cắm đúng I2C: SCL=pin19, SDA=pin20)
- VSCode + PyMakr (đã cấu hình theo README gốc)

---

## Bước 1: Thu thập dữ liệu

### Cách A: Dùng dữ liệu mẫu (synthetic) để test nhanh

```bash
cd ai
python generate_sample_data.py
```

Tạo file `sample_data.csv` với 450 mẫu (150 mẫu/class).

### Cách B: Thu thập dữ liệu thật từ DHT20

1. Trong `main.py`: **bỏ comment** dòng `import task_collect`, `task_collect.task_init()` và `event_manager.add_timer_event(..., task_collect.task_run)`. **Comment** dòng tương ứng của `task_ai`.

2. **Sync** project lên Yolo:Bit, **Soft reset**.

3. Trên Yolo:Bit:
   - **Nút A**: chuyển label (`binh_thuong` → `nong_am` → `lanh_kho` → ...)
   - **Nút B**: bật/tắt ghi mẫu
   - Khi bật ghi, mỗi chu kỳ in: `DATA,25.3,62.1,binh_thuong`

4. Trên PC, chạy:
   ```bash
   cd ai
   python collect_data.py --port COM5 --output my_data.csv
   ```
   (Thay COM5 bằng cổng serial đúng.)

5. Đặt Yolo:Bit ở các môi trường khác nhau, nhấn A để đổi label, nhấn B để bắt đầu ghi. Thu ít nhất **50 mẫu mỗi class**.

6. **Ctrl+C** để dừng và lưu CSV.

---

## Bước 2: Train model

```bash
cd ai
python train.py --data sample_data.csv
```

### Tùy chỉnh hyperparameters

```bash
python train.py --data my_data.csv --epochs 500 --lr 0.005 --batch_size 32 --hidden1 8 --hidden2 4
```

| Tham số | Mặc định | Mô tả |
|---------|---------|-------|
| `--data` | sample_data.csv | File CSV input |
| `--epochs` | 300 | Số epoch training |
| `--lr` | 0.01 | Learning rate |
| `--batch_size` | 16 | Kích thước batch |
| `--hidden1` | 8 | Số neuron hidden layer 1 |
| `--hidden2` | 4 | Số neuron hidden layer 2 |
| `--test_size` | 0.2 | Tỉ lệ test set |

### Output

- `best_model.pth` — model PyTorch tốt nhất (theo test accuracy)
- `train_config.json` — cấu hình (label names, scaler, architecture)
- `training_curves.png` — biểu đồ loss và accuracy qua các epoch
- In ra: classification report + confusion matrix

### Đánh giá kết quả

- **Accuracy > 90%**: tốt, có thể deploy.
- **Accuracy 70-90%**: cần thêm data hoặc điều chỉnh hyperparameters.
- **Accuracy < 70%**: kiểm tra data (label có đúng không? data có overlap nhiều không?).

---

## Bước 3: Export model → model.py

```bash
cd ai
python export_model.py
```

Tạo file `model.py` ở thư mục gốc project (cùng cấp `main.py`), chứa:

```python
LABELS = ["binh_thuong", "lanh_kho", "nong_am"]
SCALER_MEAN = [24.686667, 56.328889]
SCALER_STD = [7.622942, 20.354217]
W1 = [[...], ...]   # 2×8
b1 = [...]           # 8
W2 = [[...], ...]   # 8×4
b2 = [...]           # 4
W3 = [[...], ...]    # 4×3
b3 = [...]           # 3
```

### Đặc tả model.py (quan trọng)

Để `inference.py` trên Yolo:Bit đọc được, file `model.py` **phải có** đúng các biến sau:

| Biến | Kiểu | Kích thước | Mô tả |
|------|------|-----------|-------|
| `LABELS` | list[str] | [num_classes] | Tên các lớp, thứ tự khớp output |
| `SCALER_MEAN` | list[float] | [2] | Mean của [temp, humidity] từ StandardScaler |
| `SCALER_STD` | list[float] | [2] | Std của [temp, humidity] từ StandardScaler |
| `W1` | list[list[float]] | [2][hidden1] | Weights layer 1 (đã transpose) |
| `b1` | list[float] | [hidden1] | Biases layer 1 |
| `W2` | list[list[float]] | [hidden1][hidden2] | Weights layer 2 |
| `b2` | list[float] | [hidden2] | Biases layer 2 |
| `W3` | list[list[float]] | [hidden2][num_classes] | Weights layer 3 |
| `b3` | list[float] | [num_classes] | Biases layer 3 |

**Lưu ý:** `W` lưu dạng `[input_size][output_size]` (đã transpose so với PyTorch `nn.Linear` lưu `[output_size][input_size]`). Script `export_model.py` đã xử lý transpose tự động.

---

## Bước 4: Deploy lên Yolo:Bit

1. Đảm bảo `model.py` đã được tạo ở bước 3 (nằm cùng thư mục `main.py`).
2. Trong `main.py`: **bỏ comment** `task_ai`, **comment** `task_collect` (nếu đang bật).
3. **Sync project to device** (PyMakr).
4. **Soft reset** → mở Serial/REPL.
5. Xem log:
   ```
   [AI] DHT20 + inference OK, san sang.
   [AI] 25.3C 62.1% -> binh_thuong (conf=0.92)
   [AI] 34.5C 81.2% -> nong_am (conf=0.87)
   ```

---

## Cấu trúc file

```
yolobit-micropython/
├── ai/                          # Tools chạy trên PC
│   ├── requirements.txt         # pip install -r requirements.txt
│   ├── generate_sample_data.py  # Tạo data mẫu (synthetic)
│   ├── collect_data.py          # Đọc serial từ board → CSV
│   ├── train.py                 # Train Tiny NN (PyTorch)
│   ├── export_model.py          # Export → model.py
│   └── README.md                # File này
│
├── model.py                     # Tham số model (do export_model.py tạo) ← SINH VIÊN THAY FILE NÀY
├── inference.py                 # Forward pass thuần MicroPython (không sửa)
├── task_ai.py                   # Task chạy inference trên board
├── task_collect.py              # Task thu thập data từ DHT20
├── main.py                      # Đăng ký task_ai / task_collect
└── config.py                    # Chu kỳ task
```

---

## Câu hỏi thường gặp

### Tại sao không train trên Yolo:Bit luôn?

Training cần:
- Tính gradient (đạo hàm) qua backpropagation
- Lặp hàng trăm epoch, mỗi epoch duyệt toàn bộ dataset
- RAM cho optimizer state (Adam cần 2× số tham số thêm)
- Thư viện: PyTorch/TensorFlow (hàng chục MB)

ESP32 chỉ có ~200KB RAM free, MicroPython không có PyTorch. Một epoch training có thể mất hàng phút vs. mili-giây trên PC.

**Inference** (predict) thì ngược lại: chỉ cần 60 phép nhân + 15 phép cộng, < 1ms trên ESP32.

### Tại sao dùng Tiny NN thay vì TensorFlow Lite?

TFLite Micro là runtime C++ (~50-100KB). MicroPython không có binding chính thức. Với 2 features + 3 classes, Tiny NN thuần Python đủ mạnh và chỉ chiếm < 2KB RAM.

### Có thể thay đổi kiến trúc model không?

Có, nhưng cần sửa cả `train.py`, `export_model.py` **và** `inference.py` cho khớp. Với bài này giữ 2→8→4→3 là đủ. Nếu muốn thử 2→16→8→3 (157 tham số), sửa `--hidden1 16 --hidden2 8` khi train.

### Accuracy thấp, làm sao cải thiện?

1. **Thêm data**: thu thập thêm mẫu, đặc biệt ở vùng ranh giới giữa các class.
2. **Tăng epochs**: `--epochs 500` hoặc `--epochs 1000`.
3. **Giảm learning rate**: `--lr 0.005` hoặc `--lr 0.001`.
4. **Tăng hidden neurons**: `--hidden1 16 --hidden2 8`.
5. **Kiểm tra data**: label có gán đúng không? Có mẫu nhiễu không?
