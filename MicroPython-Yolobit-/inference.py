# -*- coding: utf-8 -*-
"""
Inference engine cho Tiny Neural Network trên MicroPython.
Đọc tham số từ model.py, chạy forward pass thuần Python (không cần numpy/torch).

Kiến trúc: 2 input → 8 hidden (ReLU) → 4 hidden (ReLU) → 3 output (argmax).

Cách dùng:
  from inference import predict
  label, confidence, scores = predict(25.3, 62.1)
"""
from model import LABELS, SCALER_MEAN, SCALER_STD, W1, b1, W2, b2, W3, b3

# ---- Các hàm tính toán cơ bản (thay thế numpy) ----

def _relu(x):
    """ReLU activation: max(0, x)."""
    return x if x > 0 else 0


def _matmul_add(inp, W, b):
    """
    Tính output = inp @ W + b (nhân ma trận + cộng bias).
    inp: list [input_size]
    W: list of lists [input_size][output_size]  (mỗi hàng W[i] tương ứng 1 input)
    b: list [output_size]
    return: list [output_size]
    """
    out_size = len(b)
    in_size = len(inp)
    result = [0.0] * out_size
    for j in range(out_size):
        s = b[j]
        for i in range(in_size):
            s += inp[i] * W[i][j]
        result[j] = s
    return result


def _softmax(scores):
    """Softmax để tính xác suất (dùng cho hiển thị, không ảnh hưởng argmax)."""
    max_s = max(scores)
    exps = []
    for s in scores:
        diff = s - max_s
        if diff < -20:
            exps.append(0.0)
        else:
            # xấp xỉ exp() cho MicroPython
            val = 2.718281828 ** diff
            exps.append(val)
    total = sum(exps)
    if total == 0:
        return [1.0 / len(scores)] * len(scores)
    return [e / total for e in exps]


def _argmax(lst):
    """Trả về index của phần tử lớn nhất."""
    max_val = lst[0]
    max_idx = 0
    for i in range(1, len(lst)):
        if lst[i] > max_val:
            max_val = lst[i]
            max_idx = i
    return max_idx


# ---- API chính ----

def normalize(temp, humidity):
    """Chuẩn hóa input giống StandardScaler đã dùng khi train."""
    return [
        (temp - SCALER_MEAN[0]) / SCALER_STD[0],
        (humidity - SCALER_MEAN[1]) / SCALER_STD[1],
    ]


def forward(temp, humidity):
    """
    Forward pass qua 3 layer.
    Return: (raw_scores, probabilities, class_index)
    """
    x = normalize(temp, humidity)

    # Layer 1: 2 → 8, ReLU
    x = _matmul_add(x, W1, b1)
    x = [_relu(v) for v in x]

    # Layer 2: 8 → 4, ReLU
    x = _matmul_add(x, W2, b2)
    x = [_relu(v) for v in x]

    # Layer 3: 4 → 3, raw scores (logits)
    scores = _matmul_add(x, W3, b3)

    probs = _softmax(scores)
    class_idx = _argmax(scores)

    return scores, probs, class_idx


def predict(temp, humidity):
    """
    Phân loại nhiệt độ + độ ẩm.
    Return: (label_name, confidence, scores)
      - label_name: str, tên lớp (ví dụ "binh_thuong")
      - confidence: float 0-1, xác suất của lớp được chọn
      - scores: list, raw scores của tất cả các lớp
    """
    scores, probs, class_idx = forward(temp, humidity)
    return LABELS[class_idx], probs[class_idx], scores
