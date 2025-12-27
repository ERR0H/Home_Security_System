"""
Tab: Giám Sát Toàn Cảnh (Multi-Camera Grid)
Hiển thị video từ nhiều camera cùng lúc trong grid layout 2x2
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import cv2
import numpy as np
import threading
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MonitorGridTab(ctk.CTkFrame):
    """
    Tab giám sát toàn cảnh với nhiều camera.
    
    Giao diện:
    - Bên trái: Danh sách camera với checkbox
    - Giữa/Phải: Grid layout hiển thị các camera đã chọn (2x2)
    """
    
    def __init__(self, parent, db_manager, face_recognizer, camera_manager):
        """
        Khởi tạo Monitor Grid Tab.
        
        Args:
            parent: Widget cha
            db_manager: DatabaseManager
            face_recognizer: FaceRecognizer
            camera_manager: CameraManager
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.face_recognizer = face_recognizer
        self.camera_manager = camera_manager
        
        # Trạng thái
        self.selected_cameras = {}  # {camera_id: is_selected}
        self.monitoring_cameras = {}  # {camera_id: is_monitoring}
        self.monitor_threads = {}  # {camera_id: thread}
        self.stop_monitor_events = {}  # {camera_id: threading.Event}
        self.last_detection_time = {}  # {(camera_id, user_name): datetime}
        
        self._setup_ui()
        self._load_camera_list()
        
        self.pack(fill="both", expand=True)
        
        logger.info("MonitorGridTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ==================== CỘT TRÁI: DANH SÁCH CAMERA ====================
        left_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(2, weight=1)
        
        title = ctk.CTkLabel(
            left_frame,
            text="📷 Chọn Camera",
            font=("Arial", 12, "bold")
        )
        title.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Nút điều khiển
        ctrl_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ctrl_frame.grid_columnconfigure((0, 1), weight=1)
        
        select_all_btn = ctk.CTkButton(
            ctrl_frame,
            text="✓ Chọn Tất Cả",
            command=self._select_all_cameras,
            height=30,
            font=("Arial", 9)
        )
        select_all_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        clear_all_btn = ctk.CTkButton(
            ctrl_frame,
            text="✗ Bỏ Chọn",
            command=self._clear_all_cameras,
            height=30,
            font=("Arial", 9)
        )
        clear_all_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Danh sách camera
        self.camera_list_frame = ctk.CTkScrollableFrame(left_frame)
        self.camera_list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.camera_list_frame.grid_columnconfigure(0, weight=1)
        
        # ==================== CỘT PHẢI: GRID VIDEO ====================
        right_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"), corner_radius=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        title2 = ctk.CTkLabel(
            right_frame,
            text="📹 Giám Sát Toàn Cảnh",
            font=("Arial", 12, "bold")
        )
        title2.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Grid container (2x2)
        grid_container = ctk.CTkFrame(right_frame, fg_color="transparent")
        grid_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        grid_container.grid_rowconfigure((0, 1), weight=1)
        grid_container.grid_columnconfigure((0, 1), weight=1)
        
        self.video_frames = {}  # {camera_id: label}
        self.camera_titles = {}  # {camera_id: title_label}
        
        # Tạo 4 ô video (2x2)
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        
        for row, col in positions:
            # Frame cho mỗi camera
            camera_frame = ctk.CTkFrame(grid_container, fg_color=("gray75", "gray30"), corner_radius=8)
            camera_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            camera_frame.grid_rowconfigure(1, weight=1)
            camera_frame.grid_columnconfigure(0, weight=1)
            
            # Tiêu đề camera
            title_label = ctk.CTkLabel(
                camera_frame,
                text=f"Camera {row*2 + col + 1}",
                font=("Arial", 10, "bold"),
                text_color="gray"
            )
            title_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            # Video label
            video_label = ctk.CTkLabel(
                camera_frame,
                text="Chưa chọn camera",
                fg_color=("gray70", "gray20"),
                corner_radius=5
            )
            video_label.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
            
            # Lưu trữ
            self.video_frames[row*2 + col] = video_label
            self.camera_titles[row*2 + col] = title_label
    
    def _load_camera_list(self):
        """Tải và hiển thị danh sách camera"""
        # Xóa widget cũ
        for widget in self.camera_list_frame.winfo_children():
            widget.destroy()
        
        cameras = self.db_manager.get_all_cameras()
        
        if not cameras:
            no_camera_label = ctk.CTkLabel(
                self.camera_list_frame,
                text="Chưa có camera",
                text_color="gray"
            )
            no_camera_label.pack(padx=10, pady=10)
            return
        
        for camera in cameras:
            camera_id = camera['id']
            name = camera['name']
            
            # Khởi tạo trạng thái
            if camera_id not in self.selected_cameras:
                self.selected_cameras[camera_id] = False
                self.monitoring_cameras[camera_id] = False
            
            # Frame cho checkbox + tên camera
            cam_item_frame = ctk.CTkFrame(self.camera_list_frame, fg_color="transparent")
            cam_item_frame.pack(fill="x", padx=5, pady=5)
            cam_item_frame.grid_columnconfigure(1, weight=1)
            
            # Checkbox
            checkbox = ctk.CTkCheckBox(
                cam_item_frame,
                text=name,
                command=lambda cid=camera_id: self._toggle_camera(cid),
                font=("Arial", 10)
            )
            checkbox.pack(side="left", fill="x", expand=True)
            
            # Nút start/stop
            control_btn = ctk.CTkButton(
                cam_item_frame,
                text="▶️",
                command=lambda cid=camera_id, cname=name: self._toggle_monitoring(cid, cname),
                width=40,
                height=25,
                font=("Arial", 9)
            )
            control_btn.pack(side="right", padx=5)
    
    def _toggle_camera(self, camera_id: int):
        """Chọn/bỏ chọn camera"""
        self.selected_cameras[camera_id] = not self.selected_cameras[camera_id]
        self._update_grid_display()
    
    def _select_all_cameras(self):
        """Chọn tất cả camera"""
        for camera_id in self.selected_cameras:
            self.selected_cameras[camera_id] = True
        
        # Refresh UI
        self._load_camera_list()
        self._update_grid_display()
    
    def _clear_all_cameras(self):
        """Bỏ chọn tất cả camera"""
        # Dừng tất cả monitoring
        for camera_id in list(self.monitoring_cameras.keys()):
            if self.monitoring_cameras[camera_id]:
                self._stop_camera_monitoring(camera_id)
        
        for camera_id in self.selected_cameras:
            self.selected_cameras[camera_id] = False
        
        # Refresh UI
        self._load_camera_list()
        self._update_grid_display()
    
    def _update_grid_display(self):
        """Cập nhật hiển thị grid dựa trên camera được chọn"""
        selected_cams = [cid for cid, selected in self.selected_cameras.items() if selected]
        
        # Cập nhật tiêu đề và ẩn các ô không dùng
        for idx in range(4):
            if idx < len(selected_cams):
                camera_id = selected_cams[idx]
                camera = self.db_manager.get_camera_by_id(camera_id)
                if camera:
                    self.camera_titles[idx].configure(text=f"📷 {camera['name']}")
                    self.video_frames[idx].configure(text="Nhấn ▶️ để bắt đầu")
            else:
                self.camera_titles[idx].configure(text="Không sử dụng")
                self.video_frames[idx].configure(image="", text="Chưa chọn camera")
    
    def _toggle_monitoring(self, camera_id: int, camera_name: str):
        """Bắt đầu/dừng giám sát camera"""
        if self.monitoring_cameras.get(camera_id, False):
            # Dừng monitoring
            self._stop_camera_monitoring(camera_id)
        else:
            # Bắt đầu monitoring
            self._start_camera_monitoring(camera_id, camera_name)
    
    def _start_camera_monitoring(self, camera_id: int, camera_name: str):
        """Bắt đầu giám sát camera"""
        # Lấy URL camera
        camera_info = self.db_manager.get_camera_by_id(camera_id)
        if not camera_info:
            logger.error(f"Camera {camera_id} not found")
            return
        
        # Khởi tạo events
        if camera_id not in self.stop_monitor_events:
            self.stop_monitor_events[camera_id] = threading.Event()
        
        self.stop_monitor_events[camera_id].clear()
        
        # Bắt đầu camera manager
        self.camera_manager.start_camera(camera_id, camera_info['rtsp_url'])
        
        # Khởi tạo monitoring
        self.monitoring_cameras[camera_id] = True
        self.face_recognizer.load_known_faces()
        
        # Tạo thread monitoring
        thread = threading.Thread(
            target=self._monitoring_loop,
            args=(camera_id,),
            daemon=True
        )
        self.monitor_threads[camera_id] = thread
        thread.start()
        
        logger.info(f"Started monitoring camera {camera_id}")
    
    def _stop_camera_monitoring(self, camera_id: int):
        """Dừng giám sát camera"""
        if camera_id in self.stop_monitor_events:
            self.stop_monitor_events[camera_id].set()
        
        self.monitoring_cameras[camera_id] = False
        
        # Dừng camera manager
        self.camera_manager.stop_camera(camera_id)
        
        # Chờ thread
        if camera_id in self.monitor_threads:
            self.monitor_threads[camera_id].join(timeout=2)
        
        # Xóa ảnh
        idx = self._get_camera_index(camera_id)
        if idx is not None:
            self.video_frames[idx].configure(image="", text="Nhấn ▶️ để bắt đầu")
        
        logger.info(f"Stopped monitoring camera {camera_id}")
    
    def _get_camera_index(self, camera_id: int) -> int:
        """Lấy index của camera trong grid"""
        selected_cams = [cid for cid, selected in self.selected_cameras.items() if selected]
        try:
            return selected_cams.index(camera_id)
        except ValueError:
            return None
    
    def _monitoring_loop(self, camera_id: int):
        """Luồng giám sát cho mỗi camera"""
        try:
            while not self.stop_monitor_events[camera_id].is_set() and self.monitoring_cameras.get(camera_id, False):
                # Lấy frame
                frame = self.camera_manager.get_frame(camera_id)
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                # Nhận diện khuôn mặt
                detections = self.face_recognizer.recognize(frame)
                
                # Vẽ detection
                annotated_frame = self._draw_detections(frame, detections)
                
                # Hiển thị
                idx = self._get_camera_index(camera_id)
                if idx is not None:
                    self._display_frame(annotated_frame, idx)
                
                # Ghi nhận detection
                for detection in detections:
                    self._process_detection(camera_id, detection)
                
                time.sleep(0.01)
        
        except Exception as e:
            logger.error(f"Error in monitoring loop for camera {camera_id}: {e}")
        
        finally:
            self.monitoring_cameras[camera_id] = False
    
    def _draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """Vẽ khung mặt lên frame"""
        annotated = frame.copy()
        for detection in detections:
            top, right, bottom, left = detection['location']
            name = detection['name']
            color = (0, 255, 0) if name != "Unknown" else (0, 255, 255)
            label = name if name else "Unknown"
            
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
            text_bg_coords = (left, top - 25)
            text_end_coords = (left + text_width + 10, top)
            cv2.rectangle(annotated, text_bg_coords, text_end_coords, color, -1)
            text_coords = (left + 5, top - 10)
            cv2.putText(annotated, label, text_coords, font, font_scale, (255, 255, 255), font_thickness)
        
        return annotated
    
    def _display_frame(self, frame: np.ndarray, idx: int):
        """Hiển thị frame lên grid"""
        try:
            FIXED_WIDTH = 350
            FIXED_HEIGHT = 250
            
            h, w = frame.shape[:2]
            scale = min(FIXED_WIDTH / w, FIXED_HEIGHT / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            frame_resized = cv2.resize(frame, (new_w, new_h))
            
            # Tạo canvas cố định
            canvas = np.ones((FIXED_HEIGHT, FIXED_WIDTH, 3), dtype=np.uint8) * 30
            
            y_offset = (FIXED_HEIGHT - new_h) // 2
            x_offset = (FIXED_WIDTH - new_w) // 2
            
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized
            
            # Chuyển đổi
            frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Cập nhật label
            self.video_frames[idx].configure(image=photo, text="")
            self.video_frames[idx].image = photo
        
        except Exception as e:
            logger.error(f"Error displaying frame for index {idx}: {e}")
    
    def _process_detection(self, camera_id: int, detection: dict):
        """Xử lý phát hiện"""
        try:
            name = detection['name']
            user_id = detection['user_id']
            
            # Kiểm tra 60 giây
            should_log = self._should_log_detection_memory(camera_id, name, threshold_seconds=60)
            
            if should_log:
                # Ghi database
                if name == "Unknown":
                    detection_type = 'unknown'
                else:
                    if user_id:
                        user_info = self.db_manager.get_user_by_id(user_id)
                        if user_info and user_info['category'] == 'blacklist':
                            detection_type = 'suspicious'
                        else:
                            detection_type = 'known'
                    else:
                        detection_type = 'unknown'
                
                self.db_manager.log_detection(
                    camera_id=camera_id,
                    detection_type=detection_type,
                    user_id=user_id,
                    user_name=name
                )
                
                detection_key = (camera_id, name)
                self.last_detection_time[detection_key] = datetime.now()
        
        except Exception as e:
            logger.error(f"Error processing detection: {e}")
    
    def _should_log_detection_memory(self, camera_id: int, user_name: str, threshold_seconds=60) -> bool:
        """Kiểm tra xem có nên ghi nhận hay không"""
        detection_key = (camera_id, user_name)
        current_time = datetime.now()
        
        if detection_key not in self.last_detection_time:
            return True
        
        last_time = self.last_detection_time[detection_key]
        time_diff = (current_time - last_time).total_seconds()
        
        return time_diff >= threshold_seconds
    
    def cleanup(self):
        """Dọn dẹp khi đóng tab"""
        # Dừng tất cả monitoring
        for camera_id in list(self.monitoring_cameras.keys()):
            if self.monitoring_cameras[camera_id]:
                self._stop_camera_monitoring(camera_id)
        
        logger.info("MonitorGridTab cleaned up")
