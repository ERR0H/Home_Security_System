"""
Tab 5: Thông Tin Ứng Dụng & Tác Giả
Hiển thị thông tin về ứng dụng, tác giả và các liên kết hữu ích
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)


class InfoTab(ctk.CTkFrame):
    """
    Tab thông tin ứng dụng.
    
    Hiển thị:
    - Tên ứng dụng và phiên bản
    - Tác giả
    - Mô tả chức năng
    - Liên kết hữu ích
    """
    
    def __init__(self, parent):
        """
        Khởi tạo Info Tab.
        
        Args:
            parent: Widget cha
        """
        super().__init__(parent)
        
        self._setup_ui()
        
        # Pack frame để fill parent
        self.pack(fill="both", expand=True)
        
        logger.info("InfoTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Container chính
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # ==================== TIÊU ĐỀ ỨNG DỤNG ====================
        header_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"), corner_radius=15)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        
        app_title = ctk.CTkLabel(
            header_frame,
            text="🔒 HỆ THỐNG GIÁM SÁT AN NINH HỘ GIA ĐÌNH",
            font=("Arial", 20, "bold")
        )
        app_title.pack(padx=20, pady=15)
        
        version_label = ctk.CTkLabel(
            header_frame,
            text="Phiên Bản: 1.0.0",
            font=("Arial", 12),
            text_color="gray"
        )
        version_label.pack(padx=20, pady=(0, 15))
        
        # ==================== NỘI DUNG THÔNG TIN ====================
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Tác giả
        author_section = ctk.CTkFrame(content_frame, fg_color=("gray90", "gray20"), corner_radius=10)
        author_section.pack(fill="x", padx=0, pady=10)
        author_section.grid_columnconfigure(0, weight=1)
        
        author_title = ctk.CTkLabel(
            author_section,
            text="👨‍💻 Tác Giả",
            font=("Arial", 14, "bold")
        )
        author_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        author_name = ctk.CTkLabel(
            author_section,
            text="Hoàng Hào Hùng",
            font=("Arial", 12)
        )
        author_name.pack(anchor="w", padx=20, pady=2)
        
        author_alias = ctk.CTkLabel(
            author_section,
            text="aka Mướp The Lỏ 🍃",
            font=("Arial", 12, "italic"),
            text_color="gray"
        )
        author_alias.pack(anchor="w", padx=20, pady=(2, 15))
        
        # Mô tả chức năng
        description_section = ctk.CTkFrame(content_frame, fg_color=("gray90", "gray20"), corner_radius=10)
        description_section.pack(fill="both", expand=True, padx=0, pady=10)
        description_section.grid_columnconfigure(0, weight=1)
        description_section.grid_rowconfigure(1, weight=1)
        
        desc_title = ctk.CTkLabel(
            description_section,
            text="📋 Mô Tả Ứng Dụng",
            font=("Arial", 14, "bold")
        )
        desc_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Textbox chứa mô tả
        desc_text_frame = ctk.CTkFrame(description_section)
        desc_text_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        desc_text_frame.grid_rowconfigure(0, weight=1)
        desc_text_frame.grid_columnconfigure(0, weight=1)
        
        desc_textbox = ctk.CTkTextbox(
            desc_text_frame,
            state="disabled",
            text_color="white",
            fg_color=("gray75", "gray15"),
            corner_radius=8
        )
        desc_textbox.grid(row=0, column=0, sticky="nsew")
        
        # Nội dung mô tả
        description = """Hệ Thống Giám Sát An Ninh Hộ Gia Đình (Home Security System) là một ứng dụng để giám sát camera, nhận diện khuôn mặt và ghi lại lịch sử phát hiện.

Các Tính Năng Chính:
• 📹 Giám Sát Trực Tiếp: Kết nối và hiển thị video từ camera RTSP
• 👤 Nhận Diện Khuôn Mặt: Sử dụng Zernike Moments để nhận diện
• 📷 Quản Lý Camera: Thêm, sửa, xóa và kiểm tra camera
• 👥 Quản Lý Cơ Sở Dữ Liệu Khuôn Mặt: Thêm người vào whitelist/blacklist
• 📊 Thống Kê & Lịch Sử: Xem lịch sử phát hiện và thống kê
• 🗑️ Quản Lý Dữ Liệu: Xóa dữ liệu lịch sử khi cần

Công Nghệ Sử Dụng:
• Python 3.8+
• CustomTkinter (GUI)
• OpenCV (xử lý video)
• SQLite3 (cơ sở dữ liệu)
• Mahotas (Zernike Moments)

Hỗ Trợ & Phản Hồi:
Nếu gặp vấn đề hoặc có đề xuất, vui lòng liên hệ tác giả.
"""
        
        desc_textbox.configure(state="normal")
        desc_textbox.insert("1.0", description)
        desc_textbox.configure(state="disabled")
        
        # ==================== FOOTER ====================
        footer_frame = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"), corner_radius=10)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=10)
        footer_frame.grid_columnconfigure(0, weight=1)
        
        footer_text = ctk.CTkLabel(
            footer_frame,
            text="© 2025 Hệ Thống Giám Sát An Ninh Hộ Gia Đình. Tất cả quyền được bảo lưu.",
            font=("Arial", 10),
            text_color="gray"
        )
        footer_text.pack(padx=20, pady=10)
    
    def cleanup(self):
        """Dọn dẹp khi đóng tab"""
        logger.info("InfoTab cleaned up")
