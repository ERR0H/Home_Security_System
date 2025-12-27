# 🏠 Hệ Thống Giám Sát An Ninh Hộ Gia Đình

Một ứng dụng desktop Python hiện đại cho việc giám sát an ninh hộ gia đình với khả năng nhận dạng khuôn mặt, quản lý camera và thống kê chi tiết.

## ✨ Tính Năng Chính

### 1. **Giám Sát Trực Tiếp (Monitor Center)**
   - Xem video trực tiếp từ camera được chọn
   - Vẽ khung mặt và hiển thị tên người được nhận dạng
   - Hiển thị thông tin chi tiết: loại đối tượng, độ tin cậy
   - Cảnh báo thời gian thực

### 2. **Giám Sát Đa Camera (Monitor Grid)**
   - Hiển thị video từ 4 camera cùng lúc (2x2)
   - Nhận dạng khuôn mặt trên tất cả camera
   - Thống kê phát hiện theo từng camera

### 3. **Quản Lý Camera**
   - Thêm/chỉnh sửa/xóa camera
   - Hỗ trợ URL RTSP từ các loại camera khác nhau
   - Test kết nối trước khi lưu
   - Quản lý trạng thái camera

### 4. **Cơ Sở Dữ Liệu Khuôn Mặt**
   - Thêm khuôn mặt vào danh sách trắng (whitelist) - người quen
   - Thêm khuôn mặt vào danh sách đen (blacklist) - người đáng ngờ
   - Tính toán Zernike moments cho mỗi khuôn mặt
   - Quản lý hình ảnh và tính năng

### 5. **Nhận Dạng Khuôn Mặt**
   - Sử dụng **Zernike moments** để trích xuất đặc trưng
   - Tính khoảng cách Euclidean để so khớp
   - Phân loại: Người quen (Known), Người lạ (Unknown), Tình nghi (Suspicious)
   - Độ chính xác cao, tốc độ xử lý nhanh

### 6. **Thống Kê & Lịch Sử**
   - Xem lịch sử phát hiện chi tiết
   - Lọc theo ngày (Hôm nay, 7 ngày, 30 ngày, Tất cả)
   - Thống kê tổng hợp (Tổng phát hiện, Người quen, Người lạ, Tình nghi)
   - **Hiển thị thời gian chính xác theo múi giờ Việt Nam (UTC+7)**

### 7. **Thông Tin Ứng Dụng**
   - Hướng dẫn sử dụng
   - Thông tin phiên bản
   - Liên hệ hỗ trợ

## 🛠️ Yêu Cầu Hệ Thống

- **Python**: 3.9 hoặc cao hơn
- **OS**: Windows, macOS, Linux
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **Camera/RTSP**: Hỗ trợ webcam hoặc camera IP với RTSP stream

## 📦 Cài Đặt

### 1. Clone hoặc Download Dự Án
```bash
git clone <repository-url>
cd Home_Security_System
```

### 2. Tạo Virtual Environment (Khuyến Nghị)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

## 🚀 Chạy Ứng Dụng

```bash
python main.py
```

Ứng dụng sẽ khởi động với giao diện Dark Mode. Chọn camera để bắt đầu giám sát.

## 📁 Cấu Trúc Thư Mục

```
Home_Security_System/
├── main.py                          # File chính để khởi động ứng dụng
├── requirements.txt                 # Dependencies
├── README.md                        # Hướng dẫn này
├── config/
│   └── config.py                   # Tham số cấu hình
├── src/
│   ├── database.py                 # Quản lý SQLite database
│   ├── camera_handler.py           # Xử lý camera và RTSP
│   ├── face_recognizer.py          # Nhận dạng khuôn mặt bằng Zernike moments
│   ├── zernike_utils.py            # Tiện ích tính toán Zernike moments
│   ├── gui_main.py                 # Giao diện chính & Tab Manager
│   ├── gui_monitor.py              # Tab: Giám sát 1 camera
│   ├── gui_monitor_grid.py         # Tab: Giám sát 4 camera
│   ├── gui_camera_setup.py         # Tab: Quản lý camera
│   ├── gui_face_db.py              # Tab: Quản lý khuôn mặt
│   ├── gui_statistics.py           # Tab: Thống kê & Lịch sử
│   └── gui_info.py                 # Tab: Thông tin
└── data/
    └── security_system.db          # SQLite database (tạo tự động)
```

## 🔧 Cấu Hình Camera

### Loại Camera Được Hỗ Trợ
1. **Webcam USB**: Dùng index (0, 1, 2, ...)
2. **Camera IP (RTSP)**:
   - Hikvision: `rtsp://IP:554/Streaming/Channels/101`
   - Dahua: `rtsp://IP:554/stream/main`
   - Axis: `rtsp://IP:554/axis-media/media.amp`
   - Generic: `rtsp://username:password@IP:554/live`

### Ví Dụ Thêm Camera
```
Tên Camera: Cửa Trước
RTSP URL: rtsp://192.168.1.100:554/Streaming/Channels/101
```

## 📊 Cơ Sở Dữ Liệu

### Bảng Chính
- **users**: Lưu khuôn mặt (whitelist/blacklist)
  - Zernike moments (512 chiều)
  - Hình ảnh gốc
  - Danh mục

- **cameras**: Danh sách camera
  - RTSP URL
  - Trạng thái (active/inactive)

- **detection_history**: Lịch sử phát hiện
  - Timestamp (múi giờ Việt Nam UTC+7)
  - Loại phát hiện (known/unknown/suspicious)
  - Tên người, Camera ID
  - Được sắp xếp theo thời gian mới nhất

## 🎯 Nguyên Lý Hoạt Động

### Nhận Dạng Khuôn Mặt
1. **Phát hiện khuôn mặt**: Sử dụng Haar Cascade từ OpenCV
2. **Trích xuất đặc trưng**: Tính Zernike moments (order 12)
3. **So khớp**: Dùng Euclidean distance để tìm khuôn mặt gần nhất
4. **Phân loại**:
   - Known (Người quen)
   - Suspicious (Tình nghi)
   - Unknown (Người lạ)

### Thời Gian
- **Lưu trữ**: Tất cả timestamp được lưu theo múi giờ Việt Nam (UTC+7)
- **Hiển thị**: Tự động hiển thị chính xác theo múi giờ máy tính
- **Lọc**: Các bộ lọc ngày sử dụng thời gian Việt Nam

## ⚙️ Thông Số Cấu Hình

Có thể chỉnh sửa trong `config/config.py`:
```python
# Zernike moments
ZERNIKE_ORDER = 12
ZERNIKE_RADIUS = 80

# Ngưỡng nhận dạng
KNOWN_THRESHOLD = 10.0
SUSPICIOUS_THRESHOLD = 15.0

# Camera
CAMERA_TIMEOUT = 5  # giây
FRAME_READ_INTERVAL = 0.03  # giây

# GUI
DARK_MODE = True
DEFAULT_COLOR_THEME = "blue"
```

## 🐛 Khắc Phục Sự Cố

### Lỗi: "Failed to open camera"
- Kiểm tra RTSP URL
- Kiểm tra kết nối mạng
- Kiểm tra tài khoản/mật khẩu camera

### Lỗi: "No module named 'customtkinter'"
- Chạy: `pip install --upgrade customtkinter`

### Hiệu Suất Thấp
- Giảm độ phân giải camera
- Giảm số camera được giám sát
- Đóng các ứng dụng khác

### Nhận Dạng Không Chính Xác
- Thêm nhiều ảnh khuôn mặt trong độ sáng khác nhau
- Điều chỉnh ngưỡng trong config
- Đảm bảo khuôn mặt trong database rõ ràng

## 📝 Hướng Dẫn Sử Dụng

### Bước 1: Thêm Camera
1. Mở tab **"Camera Setup"**
2. Nhập tên camera và RTSP URL
3. Click "Test Connection"
4. Nếu thành công, click "Add Camera"

### Bước 2: Thêm Khuôn Mặt
1. Mở tab **"Face Database"**
2. Chọn danh mục (Whitelist/Blacklist)
3. Nhập tên người
4. Chụp ảnh hoặc chọn từ file
5. Click "Add Face"

### Bước 3: Giám Sát
1. Mở tab **"Monitor Center"**
2. Chọn camera từ danh sách
3. Xem video và cảnh báo real-time

### Bước 4: Xem Thống Kê
1. Mở tab **"Statistics"**
2. Chọn khoảng thời gian
3. Xem lịch sử phát hiện chi tiết

## 🔐 An Ninh

### Khuyến Nghị
- Lưu database ở nơi an toàn
- Backup định kỳ file `data/security_system.db`
- Sử dụng mật khẩu mạnh cho camera IP
- Chỉ chia sẻ URL RTSP với những người tin cậy

## 📄 License

Dự án này được phát hành dưới các điều khoản của tôi

## 📧 Liên Hệ & Hỗ Trợ

- **Issues & Bug Reports**: Tạo issue trên repository
- **Đóng Góp**: Pull requests được hoan nghênh
- **Câu Hỏi**: Mở Discussion hoặc liên hệ tác giả

## 🙏 Cảm Ơn

- **OpenCV**: Xử lý ảnh và video
- **CustomTkinter**: Giao diện GUI hiện đại
- **Mahotas**: Tính Zernike moments
- **Numpy/Scikit-image**: Xử lý dữ liệu

---

**Phiên bản**: 1.0  
**Cập nhật cuối**: Tháng 12, 2025  
**Python**: 3.9+
