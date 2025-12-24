
"""
Module nhận diện khuôn mặt sử dụng Zernike Moments (mahotas)
"""
import numpy as np
import cv2
import logging
from zernike_utils import get_face_moments_zernike

logger = logging.getLogger(__name__)

class FaceRecognizer:
    THRESHOLD = 0.06  # Ngưỡng nhận diện, có thể tinh chỉnh
    RADIUS = 100
    DEGREE = 8

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.known_face_encodings = []  # Zernike vectors
        self.known_face_ids = []
        self.known_face_names = []
        self.load_known_faces()

    def load_known_faces(self):
        """Tải vector đặc trưng Zernike từ DB"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        all_users = self.db_manager.get_all_users()
        for user in all_users:
            features = user.get('features')
            if features:
                # Deserialize numpy array từ BLOB
                import pickle
                try:
                    features_array = pickle.loads(features)
                    self.known_face_encodings.append(np.array(features_array))
                    self.known_face_ids.append(user['id'])
                    self.known_face_names.append(user['name'])
                except Exception as e:
                    logger.warning(f"Failed to deserialize features for user {user['id']}: {e}")
        logger.info(f"Loaded {len(self.known_face_encodings)} known faces (Zernike).")

    def recognize(self, frame):
        """Nhận diện khuôn mặt trên frame bằng Zernike Moments"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 8)
        results = []
        for (x, y, w, h) in faces:
            roi_gray = gray[y:y+h, x:x+w]
            current_features = get_face_moments_zernike(roi_gray)
            best_match = "Unknown"
            user_id = None
            min_dist = float('inf')
            for idx, known_vec in enumerate(self.known_face_encodings):
                dist = np.linalg.norm(known_vec - current_features)
                if dist < min_dist:
                    min_dist = dist
                    best_idx = idx
            if min_dist < self.THRESHOLD:
                best_match = self.known_face_names[best_idx]
                user_id = self.known_face_ids[best_idx]
            results.append({
                'location': (y, x+w, y+h, x),  # (top, right, bottom, left)
                'name': best_match,
                'user_id': user_id,
                'distance': min_dist
            })
        return results

    def encode_face_from_image(self, image_path):
        """Trích xuất encoding Zernike từ ảnh file. Trả về vector nếu tìm thấy, ngược lại trả về None."""
        try:
            img = cv2.imread(image_path)
            if img is None:
                logger.warning(f"Không tìm thấy ảnh: {image_path}")
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 8)
            if len(faces) == 0:
                logger.warning(f"Không tìm thấy khuôn mặt trong ảnh: {image_path}")
                return None
            (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
            roi_gray = gray[y:y+h, x:x+w]
            encoding = get_face_moments_zernike(roi_gray)
            return encoding
        except Exception as e:
            logger.error(f"Error encoding face from image {image_path}: {e}")
            return None
