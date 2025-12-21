"""
File Cấu Hình Ứng Dụng (Config)
Có thể được sử dụng để tuning các tham số trong tương lai
"""

# ==================== DATABASE CONFIG ====================
DATABASE = {
    'path': 'data/security_system.db',
    'timeout': 30,  # Timeout kết nối
}

# ==================== FACE RECOGNITION CONFIG ====================
FACE_RECOGNITION = {
    'tolerance': 0.6,  # Độ chặt chẽ: 0.4 (chặt) - 0.8 (lỏng)
    'model': 'hog',  # 'hog' (nhanh) hoặc 'cnn' (chính xác)
    'known_face_encodings_cache': True,  # Cache encoding từ DB
}

# ==================== CAMERA CONFIG ====================
CAMERA = {
    'frame_skip': 0,  # Bỏ qua N frame (tăng tốc độ)
    'buffer_size': 1,  # Kích thước buffer frame
    'reconnect_interval': 5,  # Giây đợi trước khi reconnect
    'timeout': 30,  # Timeout mở kết nối
}

# ==================== GUI CONFIG ====================
GUI = {
    'theme': 'dark',  # 'dark' hoặc 'light'
    'color_scheme': 'blue',  # 'blue', 'green', 'dark-blue', etc.
    'window_width': 1400,
    'window_height': 900,
    'font_size_title': 13,
    'font_size_text': 10,
}

# ==================== MONITORING CONFIG ====================
MONITORING = {
    'alert_history_max_lines': 100,  # Giữ 100 dòng cảnh báo gần nhất
    'frame_update_interval': 10,  # ms - Cập nhật frame trên GUI
    'fps_update_interval': 30,  # Cập nhật FPS mỗi 30 frame
}

# ==================== ALERT CONFIG ====================
ALERT = {
    # Màu sắc
    'color_known': (0, 255, 0),  # BGR: Xanh lá
    'color_unknown': (0, 255, 255),  # BGR: Vàng
    'color_suspicious': (0, 0, 255),  # BGR: Đỏ
    
    # Alert text
    'text_known': 'NGƯỜI QUEN',
    'text_unknown': 'NGƯỜI LẠ',
    'text_suspicious': '⚠ TÌNH NGHI',
}

# ==================== LOGGING CONFIG ====================
LOGGING = {
    'level': 'INFO',  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/app.log',  # Tuỳ chọn: lưu log vào file
}

# ==================== STATISTICS CONFIG ====================
STATISTICS = {
    'days_today': 1,
    'days_week': 7,
    'days_month': 30,
    'history_refresh_interval': 5,  # Giây - Làm mới lịch sử
}

# ==================== ADVANCED CONFIG ====================
ADVANCED = {
    'enable_profiling': False,  # Bật profiling để debug
    'enable_gpu': False,  # Bật GPU acceleration (nếu có)
    'num_workers': 1,  # Số thread worker (mở rộng)
    'max_cameras': 16,  # Số camera tối đa
}

# ==================== NOTIFICATION CONFIG (Mở rộng) ====================
NOTIFICATION = {
    'enable_email': False,
    'email_smtp': 'smtp.gmail.com',
    'email_port': 587,
    'email_from': 'your-email@gmail.com',
    'email_password': 'your-password',
    'email_to': ['recipient@example.com'],
    
    'enable_sms': False,
    'sms_api_key': '',
    'sms_phone': '+84xxx',
    
    'enable_webhook': False,
    'webhook_url': 'http://your-server/webhook',
}

# ==================== CLOUD CONFIG (Mở rộng) ====================
CLOUD = {
    'enable_cloud_backup': False,
    'cloud_provider': 'aws',  # 'aws', 'google', 'azure'
    'cloud_bucket': 'security-backup',
    'cloud_api_key': '',
}

# Hàm load config từ file (tuỳ chọn)
def load_config_from_file(config_file: str = 'config/config.json'):
    """
    Tải cấu hình từ file JSON (nếu muốn)
    Hiện tại sử dụng file này là dict Python
    """
    import json
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Ví dụ sử dụng:
if __name__ == "__main__":
    print("FACE_RECOGNITION Tolerance:", FACE_RECOGNITION['tolerance'])
    print("Camera reconnect interval:", CAMERA['reconnect_interval'])
