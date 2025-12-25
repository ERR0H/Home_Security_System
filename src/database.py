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
    - users: Lưu thông tin người dùng (id, name, category, image_path, features, created_at)
    - cameras: Quản lý danh sách camera
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
            
            # Bảng users: Lưu thông tin người dùng + Zernike features
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,  -- 'whitelist' hoặc 'blacklist'
                    image_path TEXT,
                    features BLOB,  -- Pickle-serialized numpy array (Zernike moments)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name)
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
            cursor.execute('SELECT id, name, category, image_path, features, created_at FROM users')
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'image_path': row[3],
                    'features': row[4],
                    'created_at': row[5]
                })
            return users
        except sqlite3.Error as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin người dùng theo ID"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, name, category, image_path, features FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'category': row[2],
                    'image_path': row[3],
                    'features': row[4]
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
    
    # ==================== FACE FEATURES MANAGEMENT ====================
    
    def update_user_features(self, user_id: int, features: 'np.ndarray') -> bool:
        """
        Cập nhật vector đặc trưng Zernike cho người dùng.
        
        Args:
            user_id: ID người dùng
            features: numpy array chứa Zernike moments
        
        Returns:
            True nếu thành công
        """
        try:
            cursor = self.conn.cursor()
            # Serialize numpy array thành BLOB
            features_blob = pickle.dumps(features)
            cursor.execute('''
                UPDATE users SET features = ? WHERE id = ?
            ''', (features_blob, user_id))
            self.conn.commit()
            logger.info(f"Features updated for user {user_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating user features: {e}")
            return False
    
    def get_user_features(self, user_id: int) -> Optional['np.ndarray']:
        """
        Lấy vector đặc trưng Zernike của một người dùng.
        
        Args:
            user_id: ID người dùng
        
        Returns:
            numpy array hoặc None nếu không có
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT features FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row and row[0]:
                features = pickle.loads(row[0])
                return np.array(features)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching user features: {e}")
            return None
    
    def get_all_user_features(self) -> Dict[int, 'np.ndarray']:
        """
        Lấy tất cả vector đặc trưng của tất cả người dùng.
        
        Returns:
            Dict {user_id: features_array}
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, features FROM users WHERE features IS NOT NULL')
            features_dict = {}
            for row in cursor.fetchall():
                user_id = row[0]
                features = pickle.loads(row[1])
                features_dict[user_id] = np.array(features)
            return features_dict
        except sqlite3.Error as e:
            logger.error(f"Error fetching all user features: {e}")
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
        
    def update_camera(self, camera_id, name, rtsp_url):
        """Cập nhật thông tin camera"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE cameras 
                SET name = ?, rtsp_url = ?
                WHERE id = ?
            ''', (name, rtsp_url, camera_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating camera: {e}")
            return False
        
    def get_camera_by_id(self, camera_id):
        """Lấy thông tin camera để lấy link RTSP"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, name, rtsp_url FROM cameras WHERE id = ?", (camera_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "rtsp_url": row[2]}
            return None
        except Exception as e:
            print(f"Lỗi DB: {e}")
            return None
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
