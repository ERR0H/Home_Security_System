"""
Module nhận diện khuôn mặt sử dụng face_recognition
"""
import face_recognition
import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

class FaceRecognizer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.load_known_faces()

    def load_known_faces(self):
        """Tải encoding khuôn mặt từ DB"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        all_users = self.db_manager.get_all_users()
        for user in all_users:
            encodings = self.db_manager.get_face_encodings(user['id'])
            for enc in encodings:
                self.known_face_encodings.append(np.array(enc))
                self.known_face_ids.append(user['id'])
                self.known_face_names.append(user['name'])
        logger.info(f"Loaded {len(self.known_face_encodings)} known faces.")

    def recognize(self, frame):
        """Nhận diện khuôn mặt trên frame, trả về danh sách kết quả"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        results = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"
            user_id = None
            if True in matches:
                first_match_index = matches.index(True)
                name = self.known_face_names[first_match_index]
                user_id = self.known_face_ids[first_match_index]
            results.append({
                'location': (top, right, bottom, left),
                'name': name,
                'user_id': user_id
            })
        return results
