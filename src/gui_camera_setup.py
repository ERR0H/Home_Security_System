"""
Tab 2: Cài Đặt Camera
Quản lý danh sách camera: Thêm, Sửa, Xóa, Test kết nối RTSP
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import cv2
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CameraSetupTab(ctk.CTkFrame):
    """
    Tab quản lý camera.
    
    Giao diện:
    - Trên: Form thêm/sửa camera (Tên, RTSP URL, nút Test)
    - Dưới: Bảng danh sách camera
    """
    
    def __init__(self, parent, db_manager, camera_manager):
        """
        Khởi tạo Camera Setup Tab.
        
        Args:
            parent: Widget cha
            db_manager: DatabaseManager
            camera_manager: CameraManager
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.camera_manager = camera_manager
        
        # Trạng thái
        self.editing_camera_id = None
        self.is_testing = False
        
        self._setup_ui()
        self._load_camera_list()
        
        # Pack frame để fill parent
        self.pack(fill="both", expand=True)
        
        logger.info("CameraSetupTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # ==================== FORM PHẦN ====================
        form_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        form_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        form_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            form_frame,
            text="➕ Thêm / Sửa Camera",
            font=("Arial", 13, "bold")
        )
        title.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="w")
        
        # Tên camera
        name_label = ctk.CTkLabel(form_frame, text="Tên Camera:", font=("Arial", 11))
        name_label.grid(row=1, column=0, padx=10, pady=8, sticky="e")
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="VD: Camera Phòng Khách",
            width=200,
            height=35
        )
        self.name_entry.grid(row=1, column=1, padx=10, pady=8, sticky="ew")
        
        # RTSP URL
        url_label = ctk.CTkLabel(form_frame, text="RTSP URL:", font=("Arial", 11))
        url_label.grid(row=2, column=0, padx=10, pady=8, sticky="e")
        
        self.url_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="VD: rtsp://admin:pass@192.168.1.10:554/...",
            width=200,
            height=35
        )
        self.url_entry.grid(row=2, column=1, padx=10, pady=8, sticky="ew")
        
        # Nút điều khiển
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.grid(row=1, column=2, columnspan=2, padx=10, pady=8)
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.test_btn = ctk.CTkButton(
            button_frame,
            text="🔗 Test Kết Nối",
            command=self._test_connection,
            width=120,
            height=35,
            font=("Arial", 10)
        )
        self.test_btn.grid(row=0, column=0, padx=5)
        
        self.add_btn = ctk.CTkButton(
            button_frame,
            text="➕ Thêm",
            command=self._add_camera,
            width=80,
            height=35,
            font=("Arial", 10),
            fg_color=("green", "#1f6723")
        )
        self.add_btn.grid(row=0, column=1, padx=5)
        
        self.update_btn = ctk.CTkButton(
            button_frame,
            text="✏️ Cập Nhật",
            command=self._update_camera,
            width=100,
            height=35,
            font=("Arial", 10),
            fg_color=("blue", "#1f4788"),
            state="disabled"
        )
        self.update_btn.grid(row=0, column=2, padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="❌ Hủy",
            command=self._cancel_edit,
            width=80,
            height=35,
            font=("Arial", 10),
            state="disabled"
        )
        self.cancel_btn.grid(row=0, column=3, padx=5)
        
        # ==================== DANH SÁCH CAMERA PHẦN ====================
        list_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        title2 = ctk.CTkLabel(
            list_frame,
            text="📷 Danh Sách Camera",
            font=("Arial", 13, "bold")
        )
        title2.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Bảng camera (dùng Frame + Scrollbar)
        table_frame = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray25"))
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(table_frame, fg_color=("gray70", "gray35"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure((1, 2), weight=1)
        
        headers = ["ID", "Tên Camera", "RTSP URL", "Trạng Thái", "Hành Động"]
        for idx, header_text in enumerate(headers):
            header = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=("Arial", 11, "bold"),
                text_color="white"
            )
            header.grid(row=0, column=idx, padx=10, pady=10, sticky="ew")
        
        # Scrollable frame cho camera items
        self.camera_list_frame = ctk.CTkScrollableFrame(
            table_frame,
            fg_color=("gray85", "gray25"),
            corner_radius=0
        )
        self.camera_list_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.camera_list_frame.grid_columnconfigure((1, 2), weight=1)
    
    def _load_camera_list(self):
        """Tải và hiển thị danh sách camera"""
        # Xóa widget cũ
        for widget in self.camera_list_frame.winfo_children():
            widget.destroy()
        
        cameras = self.db_manager.get_all_cameras()
        
        if not cameras:
            no_camera_label = ctk.CTkLabel(
                self.camera_list_frame,
                text="Chưa có camera. Vui lòng thêm camera mới.",
                text_color="gray"
            )
            no_camera_label.pack(padx=10, pady=10)
            return
        
        for idx, camera in enumerate(cameras):
            row = idx
            
            # ID
            id_label = ctk.CTkLabel(
                self.camera_list_frame,
                text=str(camera['id']),
                font=("Arial", 10)
            )
            id_label.grid(row=row, column=0, padx=10, pady=8, sticky="w")
            
            # Tên
            name_label = ctk.CTkLabel(
                self.camera_list_frame,
                text=camera['name'],
                font=("Arial", 10)
            )
            name_label.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
            
            # URL (rút gọn nếu quá dài)
            url_text = camera['rtsp_url']
            if len(url_text) > 40:
                url_text = url_text[:37] + "..."
            
            url_label = ctk.CTkLabel(
                self.camera_list_frame,
                text=url_text,
                font=("Arial", 9),
                text_color="gray"
            )
            url_label.grid(row=row, column=2, padx=10, pady=8, sticky="ew")
            
            # Trạng thái
            status_text = camera['status'].upper()
            status_color = "green" if camera['status'] == "active" else "gray"
            
            status_label = ctk.CTkLabel(
                self.camera_list_frame,
                text=status_text,
                font=("Arial", 10),
                text_color=status_color
            )
            status_label.grid(row=row, column=3, padx=10, pady=8)
            
            # Nút hành động
            action_frame = ctk.CTkFrame(self.camera_list_frame, fg_color="transparent")
            action_frame.grid(row=row, column=4, padx=10, pady=8)
            
            edit_btn = ctk.CTkButton(
                action_frame,
                text="✏️ Sửa",
                command=lambda cid=camera['id'], cname=camera['name'], curl=camera['rtsp_url']: 
                    self._edit_camera(cid, cname, curl),
                width=60,
                height=30,
                font=("Arial", 9)
            )
            edit_btn.pack(side="left", padx=2)
            
            delete_btn = ctk.CTkButton(
                action_frame,
                text="🗑️ Xóa",
                command=lambda cid=camera['id']: self._delete_camera(cid),
                width=60,
                height=30,
                font=("Arial", 9),
                fg_color=("red", "#8B0000")
            )
            delete_btn.pack(side="left", padx=2)
    
    def _test_connection(self):
        """Test kết nối RTSP"""
        rtsp_url = self.url_entry.get().strip()
        
        if not rtsp_url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập RTSP URL!")
            return
        
        # Sửa lỗi chính tả phổ biến
        original_url = rtsp_url
        if rtsp_url.startswith("rstp://"):
            rtsp_url = "rtsp://" + rtsp_url[7:]
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, rtsp_url)
            messagebox.showinfo("Thông báo", f"Đã tự động sửa URL:\n{original_url}\n→ {rtsp_url}")
        
        self.is_testing = True
        self.test_btn.configure(state="disabled", text="⏳ Đang test...")
        
        # Chạy test trong thread riêng để không block GUI
        def test_rtsp():
            try:
                # Kiểm tra các định dạng URL phổ biến
                common_errors = [
                    ("rstp://", "rtsp://"),
                    ("rtsp//", "rtsp://"),
                    ("http://", "rtsp://"),
                    ("https://", "rtsps://")
                ]
                
                for wrong, correct in common_errors:
                    if rtsp_url.startswith(wrong):
                        suggestion = correct + rtsp_url[len(wrong):]
                        messagebox.showwarning("URL có thể sai", 
                            f"URL có thể bị sai định dạng:\n"
                            f"Hiện tại: {rtsp_url}\n"
                            f"Gợi ý: {suggestion}")
                
                cap = cv2.VideoCapture(rtsp_url)
                
                if not cap.isOpened():
                    messagebox.showerror("Lỗi", f"❌ Không thể mở kết nối tới:\n{rtsp_url}")
                    return
                
                # Thiết lập timeout
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # Thử đọc frame
                success = False
                attempts = 0
                max_attempts = 10
                
                for i in range(max_attempts):
                    ret, frame = cap.read()
                    attempts += 1
                    
                    if ret and frame is not None:
                        success = True
                        # Hiển thị thông tin frame
                        height, width = frame.shape[:2]
                        channels = frame.shape[2] if len(frame.shape) > 2 else 1
                        break
                
                cap.release()
                
                if success:
                    messagebox.showinfo("Thành Công", 
                        f"✅ Kết nối RTSP thành công!\n"
                        f"URL: {rtsp_url}\n"
                        f"Kích thước frame: {width}x{height}\n"
                        f"Kênh màu: {channels}")
                    logger.info(f"RTSP connection test successful: {rtsp_url}")
                else:
                    messagebox.showerror("Lỗi", 
                        f"❌ Kết nối được nhưng không đọc được frame!\n"
                        f"Đã thử {attempts} lần\n"
                        f"URL: {rtsp_url}")
                    logger.warning(f"RTSP connection test failed: Could not read frame after {attempts} attempts")
            
            except Exception as e:
                messagebox.showerror("Lỗi", 
                    f"❌ Lỗi kết nối:\n"
                    f"URL: {rtsp_url}\n"
                    f"Lỗi: {type(e).__name__}: {str(e)}\n\n"
                    f"Kiểm tra:\n"
                    f"1. Địa chỉ IP camera\n"
                    f"2. Tài khoản/mật khẩu\n"
                    f"3. Cổng RTSP (thường là 554)\n"
                    f"4. Đường dẫn stream (thường là /h264 or /main)")
                logger.error(f"RTSP connection test error: {type(e).__name__}: {e}", exc_info=True)
            
            finally:
                self.is_testing = False
                self.test_btn.configure(state="normal", text="🔗 Test Kết Nối")
        
        test_thread = threading.Thread(target=test_rtsp, daemon=True)
        test_thread.start()
    
    def _add_camera(self):
        """Thêm camera mới"""
        name = self.name_entry.get().strip()
        rtsp_url = self.url_entry.get().strip()
        
        if not name or not rtsp_url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên camera và RTSP URL!")
            return
        
        try:
            camera_id = self.db_manager.add_camera(name, rtsp_url)
            
            if camera_id:
                # Thêm vào CameraManager
                self.camera_manager.add_camera(camera_id, rtsp_url, name)
                
                messagebox.showinfo("Thành Công", f"✅ Thêm camera '{name}' thành công!")
                
                # Xóa form
                self.name_entry.delete(0, "end")
                self.url_entry.delete(0, "end")
                
                # Reload danh sách
                self._load_camera_list()
                
                logger.info(f"Camera added: {name} ({rtsp_url})")
            else:
                messagebox.showerror("Lỗi", "❌ Camera với URL này đã tồn tại!")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi thêm camera: {str(e)}")
            logger.error(f"Error adding camera: {e}")
    
    def _edit_camera(self, camera_id: int, camera_name: str, camera_url: str):
        """Chỉnh sửa camera"""
        self.editing_camera_id = camera_id
        
        # Hiển thị thông tin camera
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, camera_name)
        
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, camera_url)
        
        # Thay đổi trạng thái nút
        self.add_btn.configure(state="disabled")
        self.update_btn.configure(state="normal")
        self.cancel_btn.configure(state="normal")
    
    def _update_camera(self):
        """Cập nhật thông tin camera"""
        if not self.editing_camera_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn camera để sửa!")
            return
        
        name = self.name_entry.get().strip()
        rtsp_url = self.url_entry.get().strip()
        
        if not name or not rtsp_url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên camera và RTSP URL!")
            return
        
        try:
            # Sửa: Cập nhật trực tiếp thay vì xóa rồi thêm
            success = self.db_manager.update_camera(
                self.editing_camera_id, 
                name, 
                rtsp_url
            )
            
            if success:
                # Cập nhật trong CameraManager
                self.camera_manager.update_camera(
                    self.editing_camera_id,
                    rtsp_url=rtsp_url,
                    name=name
                )
                
                messagebox.showinfo("Thành Công", "✅ Cập nhật camera thành công!")
                
                # Reset form
                self._cancel_edit()
                self._load_camera_list()
                
                logger.info(f"Camera updated: ID {self.editing_camera_id}, {name} ({rtsp_url})")
            else:
                messagebox.showerror("Lỗi", "❌ Không tìm thấy camera để cập nhật!")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi cập nhật camera: {str(e)}")
            logger.error(f"Error updating camera: {e}")
    
    def _delete_camera(self, camera_id: int):
        """Xóa camera"""
        if messagebox.askyesno("Xác Nhận", "Bạn chắc chắn muốn xóa camera này?"):
            try:
                self.db_manager.delete_camera(camera_id)
                self.camera_manager.remove_camera(camera_id)
                
                messagebox.showinfo("Thành Công", "✅ Xóa camera thành công!")
                self._load_camera_list()
                
                logger.info(f"Camera deleted: ID {camera_id}")
            
            except Exception as e:
                messagebox.showerror("Lỗi", f"❌ Lỗi xóa camera: {str(e)}")
                logger.error(f"Error deleting camera: {e}")
    
    def _cancel_edit(self):
        """Hủy chỉnh sửa"""
        self.editing_camera_id = None
        
        self.name_entry.delete(0, "end")
        self.url_entry.delete(0, "end")
        
        self.add_btn.configure(state="normal")
        self.update_btn.configure(state="disabled")
        self.cancel_btn.configure(state="disabled")
