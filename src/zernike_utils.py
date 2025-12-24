"""
Module tiện ích trích xuất đặc trưng Zernike Moments
Được sử dụng chung bởi register.py, gui_face_db.py, và face_recognizer.py
"""

import cv2
import numpy as np
import mahotas

# Cấu hình Zernike
RADIUS = 100
DEGREE = 8

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')


def get_face_moments_zernike(img_or_roi_gray, radius=RADIUS, degree=DEGREE):
    """
    Trích xuất đặc trưng trực giao Zernike từ ảnh hoặc ROI.
    
    Args:
        img_or_roi_gray: Ảnh BGR hoặc ROI xám
        radius: Bán kính Zernike
        degree: Bậc Zernike
    
    Returns:
        Vector Zernike Moments (numpy array) hoặc None nếu không tìm thấy khuôn mặt
    """
    # Nếu input là ảnh BGR (3 kênh), phát hiện khuôn mặt
    if len(img_or_roi_gray.shape) == 3:
        gray = cv2.cvtColor(img_or_roi_gray, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 8)
        
        if len(faces) == 0:
            return None
        
        # Lấy khuôn mặt lớn nhất
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        roi_gray = gray[y:y+h, x:x+w]
    else:
        # Input đã là ROI xám
        roi_gray = img_or_roi_gray
    
    # Resize về kích thước cố định
    roi_resized = cv2.resize(roi_gray, (200, 200))
    
    # Tính Zernike Moments
    z_moments = mahotas.features.zernike_moments(roi_resized, radius, degree=degree)
    
    return np.array(z_moments)
