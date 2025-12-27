"""
Tab 1: Giám Sát (Monitor Center)
Hiển thị video trực tiếp từ camera, vẽ khung mặt, hiển thị cảnh báo
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


class MonitorTab(ctk.CTkFrame):
    """
    Tab giám sát trực tiếp.
    
    Giao diện:
    - Bên trái: Danh sách camera với nút chọn
    - Giữa: Hiển thị video chính
    - Bên phải: Thông tin, cảnh báo
    """
    
    def __init__(self, parent, db_manager, face_recognizer, camera_manager):
        """
        Khởi tạo Monitor Tab.
        
        Args:
            parent: Widget cha (Tab widget)
            db_manager: DatabaseManager
            face_recognizer: FaceRecognizer
            camera_manager: CameraManager
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.face_recognizer = face_recognizer
        self.camera_manager = camera_manager
        
        # Trạng thái
        self.selected_camera_id = None
        self.is_monitoring = False
        self.monitor_thread = None
        self.stop_monitor_event = threading.Event()
        
        # Cache ảnh để hiển thị
        # Dictionary để track lần cuối ghi nhận: {(camera_id, user_name): datetime}
        self.last_detection_time = {}
        self.current_frame = None
        self.display_image = None
        
        self._setup_ui()
        self._load_camera_list()
        
        # Pack frame để fill parent
        self.pack(fill="both", expand=True)
        
        logger.info("MonitorTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        # Layout: 3 cột
        # Cột trái: 200px, cột giữa: flexible, cột phải: 250px
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ==================== CỘT TRÁI: CAMERA LIST ====================
        left_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(2, weight=1)
        
        # Tiêu đề
        title_label = ctk.CTkLabel(
            left_frame,
            text="📷 Danh Sách Camera",
            font=("Arial", 12, "bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Nút tải lại danh sách
        refresh_btn = ctk.CTkButton(
            left_frame,
            text="🔄 Tải Lại",
            command=self._load_camera_list,
            height=30,
            font=("Arial", 10)
        )
        refresh_btn.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Danh sách camera
        self.camera_list_frame = ctk.CTkScrollableFrame(left_frame)
        self.camera_list_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.camera_list_frame.grid_columnconfigure(0, weight=1)
        
        # ==================== CỘT GIỮA: VIDEO DISPLAY ====================
        center_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"), corner_radius=10)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        center_frame.grid_rowconfigure(1, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        
        # Tiêu đề
        camera_title = ctk.CTkLabel(
            center_frame,
            text="Chọn camera để bắt đầu giám sát",
            font=("Arial", 12, "bold"),
            text_color="gray"
        )
        camera_title.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.camera_title_label = camera_title
        
        # Hình ảnh video
        self.video_label = ctk.CTkLabel(
            center_frame,
            text="",
            fg_color=("gray80", "gray30"),
            corner_radius=5
        )
        self.video_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Thống kê FPS
        info_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        info_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        info_frame.grid_columnconfigure(1, weight=1)
        
        self.info_label = ctk.CTkLabel(
            info_frame,
            text="FPS: 0 | Frame: 0",
            font=("Arial", 10),
            text_color="gray"
        )
        self.info_label.grid(row=0, column=0, sticky="w")
        
        # ==================== CỘT PHẢI: THÔNG TIN & CẢNH BÁO ====================
        right_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(2, weight=1)
        
        # Tiêu đề
        alert_title = ctk.CTkLabel(
            right_frame,
            text="⚠️ Cảnh Báo & Thông Tin",
            font=("Arial", 12, "bold")
        )
        alert_title.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Nút điều khiển
        control_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        control_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.start_btn = ctk.CTkButton(
            control_frame,
            text="▶️ Bắt Đầu",
            command=self._start_monitoring,
            height=35,
            font=("Arial", 10),
            fg_color=("green", "#1f6723")
        )
        self.start_btn.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.stop_btn = ctk.CTkButton(
            control_frame,
            text="⏹️ Dừng",
            command=self._stop_monitoring,
            height=35,
            font=("Arial", 10),
            fg_color=("red", "#8B0000"),
            state="disabled"
        )
        self.stop_btn.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        # Vùng cảnh báo
        alert_text_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        alert_text_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        alert_text_frame.grid_rowconfigure(0, weight=1)
        alert_text_frame.grid_columnconfigure(0, weight=1)
        
        self.alert_text = ctk.CTkTextbox(
            alert_text_frame,
            height=300,
            width=250,
            state="disabled",
            text_color="white",
            fg_color=("gray75", "gray15")
        )
        self.alert_text.grid(row=0, column=0, sticky="nsew")
        
        # Nút xóa cảnh báo
        clear_btn = ctk.CTkButton(
            right_frame,
            text="🗑️ Xóa Cảnh Báo",
            command=self._clear_alerts,
            height=30,
            font=("Arial", 10)
        )
        clear_btn.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
    
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
            
            # Nút camera
            btn = ctk.CTkButton(
                self.camera_list_frame,
                text=name,
                command=lambda cid=camera_id, cname=name: self._select_camera(cid, cname),
                height=50,
                font=("Arial", 10),
                fg_color=("gray70", "gray40"),
                hover_color=("gray60", "gray50")
            )
            btn.pack(fill="x", padx=5, pady=5)
    
    def _select_camera(self, camera_id: int, camera_name: str):
        """Chọn camera để giám sát"""
        # Dừng monitoring hiện tại
        if self.is_monitoring:
            self._stop_monitoring()
        
        self.selected_camera_id = camera_id
        self.camera_title_label.configure(text=f"📹 {camera_name}")
        self._add_alert(f"Đã chọn camera: {camera_name}")
        
        logger.info(f"Selected camera {camera_id}: {camera_name}")

    def _start_monitoring(self):
        if not self.selected_camera_id:
            self._add_alert("❌ Chưa chọn camera!")
            return

        # Lấy thông tin từ DB để có link RTSP
        camera_info = self.db_manager.get_camera_by_id(self.selected_camera_id)
        if not camera_info:
            self._add_alert("❌ Không tìm thấy URL camera!")
            return

        # QUAN TRỌNG: Ra lệnh cho CameraManager kết nối RTSP
        self.camera_manager.start_camera(self.selected_camera_id, camera_info['rtsp_url'])

        self.is_monitoring = True
        self.stop_monitor_event.clear()
        self.face_recognizer.load_known_faces()
        
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # Reload danh sách camera để cập nhật status
        self.after(500, self._load_camera_list)
    """
    def _start_monitoring(self):
        
        if not self.selected_camera_id:
            self._add_alert("❌ Vui lòng chọn camera trước khi bắt đầu!")
            return
        
        if self.is_monitoring:
            self._add_alert("⚠️ Đang giám sát. Hãy dừng trước khi chọn camera khác!")
            return
        
        self.is_monitoring = True
        self.stop_monitor_event.clear()
        
        # Tải lại dữ liệu khuôn mặt nếu cần
        self.face_recognizer.load_known_faces()
        
        # Bắt đầu luồng monitoring
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Cập nhật UI
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        self._add_alert(f"✅ Bắt đầu giám sát camera {self.selected_camera_id}...")
        logger.info(f"Started monitoring camera {self.selected_camera_id}")
    """
    def _monitoring_loop(self):
        """
        Luồng giám sát: Lặp vô hạn, lấy frame, nhận diện, hiển thị
        Chạy trong thread riêng để không block GUI
        """
        try:
            while not self.stop_monitor_event.is_set() and self.is_monitoring:
                # Lấy frame từ camera
                frame = self.camera_manager.get_frame(self.selected_camera_id)
                if frame is None:
                    time.sleep(0.01)
                    continue
                # Nhận diện khuôn mặt
                detections = self.face_recognizer.recognize(frame)
                # Vẽ kết quả lên frame
                annotated_frame = self._draw_detections(frame, detections)
                # Hiển thị
                self._display_frame(annotated_frame)
                # Ghi lại sự kiện cảnh báo
                for detection in detections:
                    self._process_detection(detection)
                time.sleep(0.01)
        
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            self._add_alert(f"❌ Lỗi: {str(e)}")
        
        finally:
            self.is_monitoring = False
    
    def _draw_detections(self, frame: np.ndarray, detections: list) -> np.ndarray:
        """
        Vẽ khung mặt và nhãn lên frame.
        """
        annotated = frame.copy()
        for detection in detections:
            top, right, bottom, left = detection['location']
            name = detection['name']
            # Màu sắc: người quen xanh lá, lạ vàng
            color = (0, 255, 0) if name != "Unknown" else (0, 255, 255)
            label = name if name else "Unknown"
            cv2.rectangle(annotated, (left, top), (right, bottom), color, 2)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            font_thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(label, font, font_scale, font_thickness)
            text_bg_coords = (left, top - 30)
            text_end_coords = (left + text_width + 10, top)
            cv2.rectangle(annotated, text_bg_coords, text_end_coords, color, -1)
            text_coords = (left + 5, top - 10)
            cv2.putText(annotated, label, text_coords, font, font_scale, (255, 255, 255), font_thickness)
        return annotated
    
    def _display_frame(self, frame: np.ndarray):
        """
        Hiển thị frame lên label với khung cố định (700x500).
        Chuyển từ OpenCV (BGR) sang PIL (RGB) để hiển thị trên tkinter
        """
        try:
            # Khung cố định
            FIXED_WIDTH = 700
            FIXED_HEIGHT = 500
            
            h, w = frame.shape[:2]
            
            # Resize frame để vừa với khung cố định (giữ tỷ lệ)
            scale = min(FIXED_WIDTH / w, FIXED_HEIGHT / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            frame_resized = cv2.resize(frame, (new_w, new_h))
            
            # Tạo canvas cố định và đặt frame vào giữa
            canvas = np.ones((FIXED_HEIGHT, FIXED_WIDTH, 3), dtype=np.uint8) * 30
            
            # Tính vị trí để đặt frame vào giữa
            y_offset = (FIXED_HEIGHT - new_h) // 2
            x_offset = (FIXED_WIDTH - new_w) // 2
            
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized
            
            # Chuyển BGR sang RGB
            frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            
            # Chuyển sang PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Chuyển sang PhotoImage
            photo = ImageTk.PhotoImage(pil_image)
            
            # Cập nhật label
            self.video_label.configure(image=photo, text="")
            self.video_label.image = photo
            
            # Cập nhật thông tin
            camera_info = self.camera_manager.get_camera_info(self.selected_camera_id)
            if camera_info:
                fps = camera_info.get('fps', 0)
                frame_count = camera_info.get('frame_count', 0)
                self.info_label.configure(text=f"FPS: {fps} | Frame: {frame_count}")
        
        except Exception as e:
            logger.error(f"Error displaying frame: {e}")
    
    def _process_detection(self, detection: dict):
        """Xử lý sự kiện phát hiện (ghi DB, cảnh báo)"""
        try:
            name = detection['name']
            user_id = detection['user_id']
            
            # Gọi lại thread chính để xử lý
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            self.after(0, lambda: self._safe_log_detection(
                camera_id=self.selected_camera_id,
                user_id=user_id,
                user_name=name,
                timestamp=timestamp
            ))
        
        except Exception as e:
            logger.error(f"Error processing detection: {e}")

    def _safe_log_detection(self, camera_id, user_id, user_name, timestamp):
        """Ghi detection an toàn từ thread chính"""
        try:
            if user_name == "Unknown":
                detection_type = 'unknown'
                message = "👤 Phát hiện người lạ"
            else:
                # Kiểm tra category từ database
                if user_id:
                    user_info = self.db_manager.get_user_by_id(user_id)
                    if user_info and user_info['category'] == 'blacklist':
                        detection_type = 'suspicious'
                        message = f"⚠️ CẢNH BÁO: Phát hiện người tình nghi: {user_name}"
                    else:
                        detection_type = 'known'
                        message = f"✅ Phát hiện người quen: {user_name}"
                else:
                    detection_type = 'unknown'
                    message = f"👤 Phát hiện người không xác định: {user_name}"
            
            # Kiểm tra xem có nên ghi nhận lại sau 60 giây không
            # Dùng in-memory tracking thay vì query database
            should_log = self._should_log_detection_memory(camera_id, user_name, threshold_seconds=60)
            
            if should_log:
                # Ghi vào database
                self.db_manager.log_detection(
                    camera_id=camera_id,
                    detection_type=detection_type,
                    user_id=user_id,
                    user_name=user_name
                )
                
                # Update lần ghi nhận cuối cùng trong memory
                detection_key = (camera_id, user_name)
                self.last_detection_time[detection_key] = datetime.now()
                
                # Chỉ hiển thị cảnh báo cho người lạ và tình nghi
                if detection_type != 'known':
                    self._add_alert(f"[{timestamp}] {message}")
        
        except Exception as e:
            logger.error(f"Error in safe_log_detection: {e}")
    
    def _should_log_detection_memory(self, camera_id, user_name, threshold_seconds=60) -> bool:
        """
        Kiểm tra xem có nên ghi nhận sự kiện phát hiện.
        Sử dụng in-memory tracking để tránh ghi quá nhiều.
        
        Args:
            camera_id: ID camera
            user_name: Tên người dùng
            threshold_seconds: Khoảng thời gian tối thiểu giữa các lần ghi nhận
        
        Returns:
            True nếu nên ghi nhận, False nếu đã ghi nhận gần đây
        """
        detection_key = (camera_id, user_name)
        current_time = datetime.now()
        
        # Nếu chưa bao giờ ghi nhận người này trên camera này
        if detection_key not in self.last_detection_time:
            return True
        
        last_time = self.last_detection_time[detection_key]
        time_diff = (current_time - last_time).total_seconds()
        
        # Chỉ ghi nhận nếu cách lần trước >= 60 giây
        return time_diff >= threshold_seconds

    def _stop_monitoring(self):
        """Dừng giám sát camera"""
        self.stop_monitor_event.set()
        self.is_monitoring = False
        
        # Dừng luồng đọc camera của CameraManager
        self.camera_manager.stop_camera(self.selected_camera_id)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # Xóa ảnh cũ trên UI
        self.video_label.configure(image="", text="Đã dừng giám sát")
        
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._add_alert("⏹️ Đã dừng giám sát và ngắt kết nối")
        
        # Reset tracking detections khi dừng
        self.last_detection_time.clear()
        
        # Reload danh sách camera để cập nhật status
        self.after(500, self._load_camera_list)
    
    def _add_alert(self, message: str):
        """Thêm tin nhắn cảnh báo"""
        try:
            self.alert_text.configure(state="normal")
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Thêm message
            if self.alert_text.get("1.0", "end-1c"):
                self.alert_text.insert("1.0", f"\n{message}")
            else:
                self.alert_text.insert("1.0", message)
            
            # Giới hạn dòng (giữ 100 dòng cuối cùng)
            lines = int(self.alert_text.index("end-1c").split(".")[0])
            if lines > 100:
                self.alert_text.delete("1.0", "101.0")
            
            # Scroll tới cuối
            self.alert_text.see("end")
            
            self.alert_text.configure(state="disabled")
        
        except Exception as e:
            logger.error(f"Error adding alert: {e}")
    
    def _clear_alerts(self):
        """Xóa tất cả cảnh báo"""
        self.alert_text.configure(state="normal")
        self.alert_text.delete("1.0", "end")
        self.alert_text.configure(state="disabled")
    
    def cleanup(self):
        """Dọn dẹp khi đóng tab"""
        self._stop_monitoring()
        logger.info("MonitorTab cleaned up")
