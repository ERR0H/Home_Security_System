import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.camera_info = {}
        self.captures = {}
        self.threads = {}
        self.running = {}
        self.frames = {}
        self.locks = {}  # Thêm lock cho mỗi camera

    def add_camera(self, camera_id, rtsp_url, name):
        """Thêm camera vào quản lý nhưng chưa khởi động"""
        self.camera_info[camera_id] = {
            'name': name,
            'rtsp_url': rtsp_url,
            'status': 'inactive'
        }
        logger.info(f"Camera {camera_id} added to manager.")

    def remove_camera(self, camera_id):
        """Xóa camera khỏi quản lý"""
        if camera_id in self.running and self.running[camera_id]:
            self.stop_camera(camera_id)
        
        self.camera_info.pop(camera_id, None)
        self.captures.pop(camera_id, None)
        self.threads.pop(camera_id, None)
        self.frames.pop(camera_id, None)
        self.running.pop(camera_id, None)
        self.locks.pop(camera_id, None)
        logger.info(f"Camera {camera_id} removed from manager.")

    def update_camera(self, camera_id, rtsp_url=None, name=None):
        """Cập nhật thông tin camera"""
        if camera_id in self.camera_info:
            if rtsp_url:
                self.camera_info[camera_id]['rtsp_url'] = rtsp_url
            if name:
                self.camera_info[camera_id]['name'] = name
                
            # Nếu camera đang chạy, cần restart với URL mới
            if camera_id in self.running and self.running[camera_id]:
                self.stop_camera(camera_id)
                self.start_camera(camera_id)
            
            logger.info(f"Camera {camera_id} updated.")

    def _update_frame(self, camera_id):
        """Đọc frame từ camera với xử lý lỗi"""
        cap = self.captures[camera_id]
        error_count = 0
        max_errors = 5
        
        while self.running.get(camera_id, False):
            try:
                ret, frame = cap.read()
                if ret and frame is not None:
                    with self.locks[camera_id]:  # Sử dụng lock
                        self.frames[camera_id] = frame
                    error_count = 0
                else:
                    error_count += 1
                    logger.warning(f"Camera {camera_id}: Failed to read frame ({error_count}/{max_errors})")
                    
                    # Nếu quá nhiều lỗi, thử reconnect
                    if error_count >= max_errors:
                        logger.error(f"Camera {camera_id}: Too many errors, attempting reconnect...")
                        break
                
                time.sleep(0.03)
                
            except Exception as e:
                logger.error(f"Camera {camera_id}: Error in update_frame: {e}")
                time.sleep(1)
        
        # Cleanup
        cap.release()
        with self.locks[camera_id]:
            self.frames[camera_id] = None
        self.running[camera_id] = False
    
    def start_camera(self, camera_id, rtsp_url):
        if camera_id in self.captures:
            return
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            logger.error(f"Failed to open camera {camera_id}: {rtsp_url}")
            return
        
        self.captures[camera_id] = cap
        self.running[camera_id] = True
        self.frames[camera_id] = None
        self.locks[camera_id] = threading.Lock()  # Thêm lock
        
        t = threading.Thread(target=self._update_frame, args=(camera_id,), daemon=True)
        self.threads[camera_id] = t
        t.start()
        logger.info(f"Camera {camera_id} started.")

    def get_frame(self, camera_id):
        """Lấy frame an toàn với thread"""
        if camera_id in self.locks:
            with self.locks[camera_id]:
                return self.frames.get(camera_id, None)
        return None

    def stop_camera(self, camera_id):
        self.running[camera_id] = False
        if camera_id in self.threads:
            self.threads[camera_id].join(timeout=1)
        if camera_id in self.captures:
            self.captures[camera_id].release()
        self.captures.pop(camera_id, None)
        self.threads.pop(camera_id, None)
        self.frames.pop(camera_id, None)
        self.running.pop(camera_id, None)
        logger.info(f"Camera {camera_id} stopped.")

    def stop_all(self):
        for cam_id in list(self.captures.keys()):
            self.stop_camera(cam_id)

    def get_camera_info(self, camera_id):
        """Lấy thông tin camera"""
        if camera_id in self.camera_info:
            return self.camera_info[camera_id].copy()
        return None