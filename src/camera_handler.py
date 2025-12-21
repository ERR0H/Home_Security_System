"""
Module quản lý camera: lấy luồng video từ RTSP/USB
"""
import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.captures = {}
        self.threads = {}
        self.running = {}
        self.frames = {}

    def start_camera(self, camera_id, rtsp_url):
        if camera_id in self.captures:
            return
        cap = cv2.VideoCapture(rtsp_url)
        self.captures[camera_id] = cap
        self.running[camera_id] = True
        self.frames[camera_id] = None
        t = threading.Thread(target=self._update_frame, args=(camera_id,), daemon=True)
        self.threads[camera_id] = t
        t.start()
        logger.info(f"Camera {camera_id} started.")

    def _update_frame(self, camera_id):
        cap = self.captures[camera_id]
        while self.running[camera_id]:
            ret, frame = cap.read()
            if ret:
                self.frames[camera_id] = frame
            else:
                time.sleep(0.1)
        cap.release()

    def get_frame(self, camera_id):
        return self.frames.get(camera_id, None)

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
