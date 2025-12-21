"""
Module quản lý cơ sở dữ liệu SQLite3
Lưu trữ: Thông tin người dùng, khuôn mặt, lịch sử phát hiện
"""

import sqlite3
import pickle
import os
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Quản lý cơ sở dữ liệu SQLite3 cho hệ thống giám sát an ninh.
    
    Bảng:
    - users: Lưu thông tin người dùng (id, name, category, created_at)
    - face_encodings: Lưu vector mã hóa khuôn mặt (id, user_id, encoding)
    - detection_history: Lưu lịch sử phát hiện (id, user_id, camera_id, timestamp, detection_type)
    """
    
    def __init__(self, db_path: str = "data/security_system.db"):
        """
        Khởi tạo kết nối cơ sở dữ liệu.
        
        Args:
            db_path: Đường dẫn tới file SQLite database
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Khởi tạo các bảng nếu chưa tồn tại"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Bảng users: Lưu thông tin người dùng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,  -- 'whitelist' hoặc 'blacklist'
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name)
                )
            ''')
            
            # Bảng face_encodings: Lưu vector đặc trưng khuôn mặt
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS face_encodings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    encoding BLOB NOT NULL,  -- Pickle-serialized numpy array
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Bảng cameras: Quản lý danh sách camera
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    rtsp_url TEXT NOT NULL,
                    status TEXT DEFAULT 'inactive',  -- 'active' hoặc 'inactive'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(rtsp_url)
                )
            ''')
            
            # Bảng detection_history: Lưu lịch sử phát hiện
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    camera_id INTEGER NOT NULL,
                    detection_type TEXT NOT NULL,  -- 'known', 'unknown', 'suspicious'
                    user_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY(camera_id) REFERENCES cameras(id) ON DELETE CASCADE
                )
            ''')
            
            self.conn.commit()
            logger.info(f"Database initialized successfully at {self.db_path}")
        
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    # ==================== USER MANAGEMENT ====================
    
    def add_user(self, name: str, category: str, image_path: str = None) -> int:
        """
        Thêm người dùng mới vào cơ sở dữ liệu.
        
        Args:
            name: Tên người dùng
            category: 'whitelist' hoặc 'blacklist'
            image_path: Đường dẫn ảnh chân dung
        
        Returns:
            ID của người dùng vừa thêm
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, category, image_path)
                VALUES (?, ?, ?)
            ''', (name, category, image_path))
            self.conn.commit()
            logger.info(f"User '{name}' added with ID {cursor.lastrowid}")
            return cursor.lastrowid
        
        except sqlite3.IntegrityError:
            logger.warning(f"User '{name}' already exists")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """Lấy danh sách tất cả người dùng"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, name, category, image_path, created_at FROM users')
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'image_path': row[3],
                    'created_at': row[4]
                })
            return users
        except sqlite3.Error as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng theo ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, name, category, image_path FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'image_path': row[3]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching user by ID: {e}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """Xóa người dùng và tất cả dữ liệu liên quan"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            self.conn.commit()
            logger.info(f"User {user_id} deleted")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def update_user_category(self, user_id: int, category: str) -> bool:
        """Cập nhật loại phân loại người dùng"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE users SET category = ? WHERE id = ?', (category, user_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating user category: {e}")
            return False
    
    # ==================== FACE ENCODING MANAGEMENT ====================
    
    def add_face_encoding(self, user_id: int, encoding: 'np.ndarray') -> bool:
        """
        Lưu vector mã hóa khuôn mặt.
        
        Args:
            user_id: ID người dùng
            encoding: numpy array từ face_recognition
        
        Returns:
            True nếu thành công
        """
        try:
            cursor = self.conn.cursor()
            # Serialize numpy array thành BLOB
            encoding_blob = pickle.dumps(encoding)
            cursor.execute('''
                INSERT INTO face_encodings (user_id, encoding)
                VALUES (?, ?)
            ''', (user_id, encoding_blob))
            self.conn.commit()
            logger.info(f"Face encoding added for user {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding face encoding: {e}")
            return False
    
    def get_face_encodings(self, user_id: int) -> List:
        """Lấy tất cả encoding của một người dùng"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT encoding FROM face_encodings WHERE user_id = ?
            ''', (user_id,))
            encodings = []
            for row in cursor.fetchall():
                encoding = pickle.loads(row[0])
                encodings.append(encoding)
            return encodings
        except sqlite3.Error as e:
            logger.error(f"Error fetching face encodings: {e}")
            return []
    
    def get_all_face_encodings(self) -> Dict[int, List]:
        """Lấy tất cả encoding của tất cả người dùng (dạng dict)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM users')
            users = cursor.fetchall()
            
            encodings_dict = {}
            for user in users:
                user_id = user[0]
                encodings = self.get_face_encodings(user_id)
                if encodings:
                    encodings_dict[user_id] = encodings
            
            return encodings_dict
        except sqlite3.Error as e:
            logger.error(f"Error fetching all face encodings: {e}")
            return {}
    
    # ==================== CAMERA MANAGEMENT ====================
    
    def add_camera(self, name: str, rtsp_url: str) -> Optional[int]:
        """Thêm camera mới"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO cameras (name, rtsp_url, status)
                VALUES (?, ?, 'inactive')
            ''', (name, rtsp_url))
            self.conn.commit()
            logger.info(f"Camera '{name}' added with ID {cursor.lastrowid}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Camera with URL '{rtsp_url}' already exists")
            return None
        except sqlite3.Error as e:
            logger.error(f"Error adding camera: {e}")
            return None
    
    def get_all_cameras(self) -> List[Dict]:
        """Lấy danh sách tất cả camera"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, name, rtsp_url, status FROM cameras')
            cameras = []
            for row in cursor.fetchall():
                cameras.append({
                    'id': row[0],
                    'name': row[1],
                    'rtsp_url': row[2],
                    'status': row[3]
                })
            return cameras
        except sqlite3.Error as e:
            logger.error(f"Error fetching cameras: {e}")
            return []
    
    def delete_camera(self, camera_id: int) -> bool:
        """Xóa camera"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM cameras WHERE id = ?', (camera_id,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting camera: {e}")
            return False
    
    def update_camera_status(self, camera_id: int, status: str) -> bool:
        """Cập nhật trạng thái camera (active/inactive)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE cameras SET status = ? WHERE id = ?', (status, camera_id))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating camera status: {e}")
            return False
    
    # ==================== DETECTION HISTORY ====================
    
    def log_detection(self, camera_id: int, detection_type: str, user_id: int = None, user_name: str = None) -> bool:
        """
        Ghi lại sự kiện phát hiện.
        
        Args:
            camera_id: ID camera
            detection_type: 'known', 'unknown', hoặc 'suspicious'
            user_id: ID người dùng (nếu có)
            user_name: Tên người dùng (nếu có)
        
        Returns:
            True nếu thành công
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO detection_history (user_id, camera_id, detection_type, user_name, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, camera_id, detection_type, user_name))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging detection: {e}")
            return False
    
    def get_detection_history(self, days: int = 1, camera_id: int = None) -> List[Dict]:
        """
        Lấy lịch sử phát hiện trong N ngày gần nhất.
        
        Args:
            days: Số ngày (mặc định 1)
            camera_id: Lọc theo camera (nếu có)
        
        Returns:
            Danh sách các sự kiện phát hiện
        """
        try:
            cursor = self.conn.cursor()
            
            if camera_id:
                cursor.execute('''
                    SELECT id, user_name, camera_id, detection_type, timestamp
                    FROM detection_history
                    WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                      AND camera_id = ?
                    ORDER BY timestamp DESC
                ''', (days, camera_id))
            else:
                cursor.execute('''
                    SELECT id, user_name, camera_id, detection_type, timestamp
                    FROM detection_history
                    WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                ''', (days,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'user_name': row[1],
                    'camera_id': row[2],
                    'detection_type': row[3],
                    'timestamp': row[4]
                })
            return history
        except sqlite3.Error as e:
            logger.error(f"Error fetching detection history: {e}")
            return []
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Thống kê các sự kiện phát hiện trong N ngày.
        
        Args:
            days: Số ngày
        
        Returns:
            Dict chứa các thống kê
        """
        try:
            cursor = self.conn.cursor()
            
            # Tổng số phát hiện
            cursor.execute('''
                SELECT COUNT(*) FROM detection_history
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
            ''', (days,))
            total_detections = cursor.fetchone()[0]
            
            # Phân loại phát hiện
            cursor.execute('''
                SELECT detection_type, COUNT(*) FROM detection_history
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                GROUP BY detection_type
            ''', (days,))
            detection_counts = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Người lạ được phát hiện nhiều nhất
            cursor.execute('''
                SELECT user_name, COUNT(*) as count FROM detection_history
                WHERE datetime(timestamp) >= datetime('now', '-' || ? || ' days')
                  AND detection_type IN ('unknown', 'suspicious')
                GROUP BY user_name
                ORDER BY count DESC
                LIMIT 5
            ''', (days,))
            top_unknowns = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return {
                'total_detections': total_detections,
                'detection_counts': detection_counts,
                'top_unknowns': top_unknowns
            }
        except sqlite3.Error as e:
            logger.error(f"Error fetching statistics: {e}")
            return {}
    
    def close(self):
        """Đóng kết nối cơ sở dữ liệu"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Test code
if __name__ == "__main__":
    db = DatabaseManager()
    print("Database initialized successfully!")
    db.close()
