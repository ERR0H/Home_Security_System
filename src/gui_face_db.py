"""
Tab 3: Quản Lý Khuôn Mặt (Face Database)
Thêm người mới, upload ảnh, chọn whitelist/blacklist, xem danh sách
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import cv2
import logging
import os
from typing import Optional
from zernike_utils import get_face_moments_zernike

logger = logging.getLogger(__name__)


class FaceDBTab(ctk.CTkFrame):
    """
    Tab quản lý cơ sở dữ liệu khuôn mặt.
    
    Giao diện:
    - Trên trái: Upload ảnh + preview
    - Trên phải: Form nhập thông tin
    - Dưới: Danh sách người đã thêm
    """
    
    def __init__(self, parent, db_manager, face_recognizer):
        """
        Khởi tạo Face Database Tab.
        
        Args:
            parent: Widget cha
            db_manager: DatabaseManager
            face_recognizer: FaceRecognizer
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.face_recognizer = face_recognizer
        
        # Trạng thái
        self.selected_image_path = None
        self.preview_image = None
        
        self._setup_ui()
        self._load_user_list()
        
        # Pack frame để fill parent
        self.pack(fill="both", expand=True)
        
        logger.info("FaceDBTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # ==================== PHẦN FORM ====================
        form_container = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        form_container.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        form_container.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            form_container,
            text="➕ Thêm Người Mới",
            font=("Arial", 13, "bold")
        )
        title.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="w")
        
        # --- Cột trái: Upload ảnh ---
        upload_frame = ctk.CTkFrame(form_container, fg_color=("gray80", "gray30"), corner_radius=10)
        upload_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        upload_frame.grid_rowconfigure((0, 1, 2), weight=0)
        
        # Preview ảnh
        self.image_label = ctk.CTkLabel(
            upload_frame,
            text="📷 Chọn ảnh chân dung",
            width=180,
            height=180,
            fg_color=("gray70", "gray40"),
            corner_radius=5,
            font=("Arial", 10),
            text_color="gray"
        )
        self.image_label.grid(row=0, column=0, padx=10, pady=10)
        
        # Nút chọn ảnh
        choose_btn = ctk.CTkButton(
            upload_frame,
            text="📁 Chọn Ảnh",
            command=self._choose_image,
            height=40,
            font=("Arial", 11)
        )
        choose_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Thông tin ảnh
        self.image_info_label = ctk.CTkLabel(
            upload_frame,
            text="Chưa chọn ảnh",
            font=("Arial", 9),
            text_color="gray"
        )
        self.image_info_label.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # --- Cột phải: Form nhập thông tin ---
        info_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        info_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")
        info_frame.grid_columnconfigure(1, weight=1)
        
        # Tên người
        name_label = ctk.CTkLabel(info_frame, text="Tên Người:", font=("Arial", 11))
        name_label.grid(row=0, column=0, padx=10, pady=8, sticky="e")
        
        self.name_entry = ctk.CTkEntry(
            info_frame,
            placeholder_text="VD: Nguyễn Văn A",
            width=250,
            height=35
        )
        self.name_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=8, sticky="ew")
        
        # Phân loại
        category_label = ctk.CTkLabel(info_frame, text="Phân Loại:", font=("Arial", 11))
        category_label.grid(row=1, column=0, padx=10, pady=8, sticky="e")
        
        self.category_var = ctk.StringVar(value="whitelist")
        
        category_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        category_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=8, sticky="w")
        category_frame.grid_columnconfigure((0, 1), weight=0)
        
        whitelist_radio = ctk.CTkRadioButton(
            category_frame,
            text="Người Quen (Whitelist)",
            variable=self.category_var,
            value="whitelist",
            font=("Arial", 10)
        )
        whitelist_radio.grid(row=0, column=0, padx=10)
        
        blacklist_radio = ctk.CTkRadioButton(
            category_frame,
            text="Người Tình Nghi (Blacklist)",
            variable=self.category_var,
            value="blacklist",
            font=("Arial", 10)
        )
        blacklist_radio.grid(row=0, column=1, padx=10)
        
        # Nút điều khiển
        button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=15)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        add_btn = ctk.CTkButton(
            button_frame,
            text="➕ Thêm Người",
            command=self._add_person,
            height=40,
            font=("Arial", 11),
            fg_color=("green", "#1f6723")
        )
        add_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Xóa",
            command=self._clear_form,
            height=40,
            font=("Arial", 11)
        )
        clear_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # ==================== DANH SÁCH NGƯỜI ====================
        list_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        title2 = ctk.CTkLabel(
            list_frame,
            text="👥 Danh Sách Người",
            font=("Arial", 13, "bold")
        )
        title2.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Bảng người
        table_frame = ctk.CTkFrame(list_frame, fg_color=("gray85", "gray25"))
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(table_frame, fg_color=("gray70", "gray35"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        headers = ["ID", "Tên Người", "Phân Loại", "Ngày Thêm", "Ảnh", "Hành Động"]
        for idx, header_text in enumerate(headers):
            header = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=("Arial", 11, "bold"),
                text_color="white"
            )
            header.grid(row=0, column=idx, padx=10, pady=10, sticky="ew")
        
        # Configure columns để căn đối (thêm minsize cho scrollbar compensation)
        header_frame.grid_columnconfigure(0, weight=0, minsize=40)   # ID
        header_frame.grid_columnconfigure(1, weight=2, minsize=150)  # Tên
        header_frame.grid_columnconfigure(2, weight=1, minsize=100)  # Phân loại
        header_frame.grid_columnconfigure(3, weight=1, minsize=90)   # Ngày
        header_frame.grid_columnconfigure(4, weight=0, minsize=50)   # Ảnh
        header_frame.grid_columnconfigure(5, weight=1, minsize=150)  # Hành động
        
        # Scrollable frame cho user items
        self.user_list_frame = ctk.CTkScrollableFrame(
            table_frame,
            fg_color=("gray85", "gray25"),
            corner_radius=0
        )
        self.user_list_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        # Configure columns để căn đối với header (thêm minsize tương tự)
        self.user_list_frame.grid_columnconfigure(0, weight=0, minsize=40)
        self.user_list_frame.grid_columnconfigure(1, weight=2, minsize=150)
        self.user_list_frame.grid_columnconfigure(2, weight=1, minsize=100)
        self.user_list_frame.grid_columnconfigure(3, weight=1, minsize=90)
        self.user_list_frame.grid_columnconfigure(4, weight=0, minsize=50)
        self.user_list_frame.grid_columnconfigure(5, weight=1, minsize=150)
    
    def _choose_image(self):
        """Chọn file ảnh"""
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh chân dung",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        
        if file_path:
            # Normalize path (convert / to \ on Windows)
            normalized_path = os.path.normpath(file_path)
            
            # Check if file exists
            if not os.path.exists(normalized_path):
                messagebox.showerror("Lỗi", f"❌ File không tồn tại:\n{normalized_path}")
                return
            
            self.selected_image_path = normalized_path
            self._show_image_preview(normalized_path)
    
    def _show_image_preview(self, image_path: str):
        """Hiển thị preview ảnh"""
        try:
            # Normalize path
            image_path = os.path.normpath(image_path)
            
            # Đọc ảnh bằng OpenCV
            img = cv2.imread(image_path)
            
            if img is None:
                messagebox.showerror("Lỗi", "❌ Không thể đọc file ảnh!")
                return
            
            # Chuyển BGR sang RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Resize để vừa với label (180x180)
            h, w = img_rgb.shape[:2]
            scale = min(180 / w, 180 / h)
            img_resized = cv2.resize(img_rgb, (int(w * scale), int(h * scale)))
            
            # Chuyển sang PIL Image
            pil_image = Image.fromarray(img_resized)
            
            # Sử dụng CTkImage thay vì PhotoImage
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(180, 180))
            
            # Hiển thị
            self.image_label.configure(image=ctk_image, text="")
            self.image_label.image = ctk_image
            
            # Cập nhật thông tin
            file_name = image_path.split("/")[-1]
            self.image_info_label.configure(text=f"✅ {file_name}")
            
            logger.info(f"Image preview loaded: {image_path}")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi tải ảnh: {str(e)}")
            logger.error(f"Error loading image preview: {e}")
    
    def _add_person(self):
        """Thêm người mới"""
        name = self.name_entry.get().strip()
        category = self.category_var.get()
        
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên người!")
            return
        
        if not self.selected_image_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ảnh chân dung!")
            return
        
        try:
            # Đọc ảnh
            img = cv2.imread(self.selected_image_path)
            if img is None:
                messagebox.showerror("Lỗi", f"Không tìm thấy ảnh: {self.selected_image_path}")
                return
            # Trích xuất đặc trưng Zernike
            encoding = get_face_moments_zernike(img)
            if encoding is None:
                messagebox.showwarning("Cảnh báo", "Không tìm thấy khuôn mặt trong ảnh!")
                return
            # Thêm vào DB
            user_id = self.db_manager.add_user(name, category, self.selected_image_path)
            if user_id is None:
                messagebox.showwarning("Cảnh báo", "Tên người đã tồn tại!")
                return
            # Lưu features (thay vì encoding)
            self.db_manager.update_user_features(user_id, encoding)
            # Reload features từ DB
            self.face_recognizer.load_known_faces()
            messagebox.showinfo("Thành Công", f"✅ Thêm '{name}' thành công!")
            self._clear_form()
            self._load_user_list()
            logger.info(f"Person added: {name} ({category})")
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi thêm người: {str(e)}")
            logger.error(f"Error adding person: {e}")
    
    def _load_user_list(self):
        """Tải và hiển thị danh sách người"""
        # Xóa widget cũ
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        users = self.db_manager.get_all_users()
        
        if not users:
            no_user_label = ctk.CTkLabel(
                self.user_list_frame,
                text="Chưa có người nào. Vui lòng thêm người mới.",
                text_color="gray"
            )
            no_user_label.pack(padx=10, pady=10)
            return
        
        for idx, user in enumerate(users):
            # ID
            id_label = ctk.CTkLabel(
                self.user_list_frame,
                text=str(user['id']),
                font=("Arial", 10),
                justify="center"
            )
            id_label.grid(row=idx, column=0, padx=5, pady=8, sticky="ew")
            
            # Tên
            name_label = ctk.CTkLabel(
                self.user_list_frame,
                text=user['name'],
                font=("Arial", 10)
            )
            name_label.grid(row=idx, column=1, padx=10, pady=8, sticky="w")
            
            # Phân loại
            category_text = "Người Quen" if user['category'] == 'whitelist' else "Tình Nghi"
            category_color = "green" if user['category'] == 'whitelist' else "red"
            
            category_label = ctk.CTkLabel(
                self.user_list_frame,
                text=category_text,
                font=("Arial", 10),
                text_color=category_color,
                justify="center"
            )
            category_label.grid(row=idx, column=2, padx=5, pady=8, sticky="ew")
            
            # Ngày thêm
            created_at = user.get('created_at', 'N/A')
            if created_at:
                created_at = created_at.split(" ")[0]  # Chỉ lấy phần ngày
            
            date_label = ctk.CTkLabel(
                self.user_list_frame,
                text=created_at,
                font=("Arial", 9),
                text_color="gray",
                justify="center"
            )
            date_label.grid(row=idx, column=3, padx=5, pady=8, sticky="ew")
            
            # Nút xem ảnh
            view_img_btn = ctk.CTkButton(
                self.user_list_frame,
                text="📄",
                command=lambda img_path=user['image_path']: self._view_user_image(img_path),
                width=40,
                height=30,
                font=("Arial", 11)
            )
            view_img_btn.grid(row=idx, column=4, padx=5, pady=8, sticky="ew")
            
            # Nút hành động
            action_frame = ctk.CTkFrame(self.user_list_frame, fg_color="transparent")
            action_frame.grid(row=idx, column=5, padx=5, pady=8, sticky="ew")
            action_frame.grid_columnconfigure((0, 1, 2), weight=1)
            
            toggle_btn = ctk.CTkButton(
                action_frame,
                text="🔄 Đổi" if user['category'] == 'whitelist' else "✅ Quen",
                command=lambda uid=user['id'], cat=user['category']: self._toggle_category(uid, cat),
                width=60,
                height=30,
                font=("Arial", 9)
            )
            toggle_btn.grid(row=0, column=0, padx=2, sticky="ew")
            
            delete_btn = ctk.CTkButton(
                action_frame,
                text="🗑️ Xóa",
                command=lambda uid=user['id']: self._delete_person(uid),
                width=60,
                height=30,
                font=("Arial", 9),
                fg_color=("red", "#8B0000")
            )
            delete_btn.grid(row=0, column=1, padx=2, sticky="ew")
    
    def _toggle_category(self, user_id: int, current_category: str):
        """Thay đổi phân loại người (whitelist <-> blacklist)"""
        new_category = "blacklist" if current_category == "whitelist" else "whitelist"
        
        try:
            self.db_manager.update_user_category(user_id, new_category)
            
            # Reload features từ DB
            self.face_recognizer.load_known_faces()
            
            messagebox.showinfo("Thành Công", "✅ Cập nhật phân loại thành công!")
            self._load_user_list()
            
            logger.info(f"User {user_id} category changed to {new_category}")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi cập nhật: {str(e)}")
            logger.error(f"Error toggling category: {e}")
    
    def _delete_person(self, user_id: int):
        """Xóa người"""
        if messagebox.askyesno("Xác Nhận", "Bạn chắc chắn muốn xóa người này?"):
            try:
                self.db_manager.delete_user(user_id)
                
                # Reload features từ DB
                self.face_recognizer.load_known_faces()
                
                messagebox.showinfo("Thành Công", "✅ Xóa người thành công!")
                self._load_user_list()
                
                logger.info(f"Person deleted: ID {user_id}")
            
            except Exception as e:
                messagebox.showerror("Lỗi", f"❌ Lỗi xóa người: {str(e)}")
                logger.error(f"Error deleting person: {e}")
    
    def _view_user_image(self, image_path: str):
        """Hiển thị ảnh của người dùng"""
        if not image_path:
            messagebox.showwarning("Cảnh báo", "Người dùng này không có ảnh lưu!")
            return
        
        try:
            # Kiểm tra file tồn tại
            if not os.path.exists(image_path):
                messagebox.showerror("Lỗi", f"Ảnh không tồn tại:\n{image_path}")
                return
            
            # Đọc và hiển thị ảnh trong cửa sổ mới
            img = cv2.imread(image_path)
            if img is None:
                messagebox.showerror("Lỗi", "Không thể đọc file ảnh!")
                return
            
            # Chuyển BGR sang RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Tạo cửa sổ mới để hiển thị
            view_window = ctk.CTkToplevel(self)
            view_window.title("Xem Ảnh Người Dùng")
            view_window.geometry("600x600")
            
            # Resize ảnh để vừa với cửa sổ
            h, w = img_rgb.shape[:2]
            scale = min(550 / w, 550 / h)
            img_resized = cv2.resize(img_rgb, (int(w * scale), int(h * scale)))
            
            # Chuyển sang PIL Image
            pil_image = Image.fromarray(img_resized)
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(550, 550))
            
            # Hiển thị ảnh
            img_label = ctk.CTkLabel(view_window, image=ctk_image, text="")
            img_label.image = ctk_image  # Giữ reference
            img_label.pack(padx=10, pady=10)
            
            # Thông tin ảnh
            file_name = os.path.basename(image_path)
            info_label = ctk.CTkLabel(
                view_window,
                text=f"📁 {file_name}",
                font=("Arial", 10),
                text_color="gray"
            )
            info_label.pack(pady=5)
            
            logger.info(f"Image viewed: {image_path}")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi xem ảnh: {str(e)}")
            logger.error(f"Error viewing image: {e}")
    
    def _clear_form(self):
        """Xóa form"""
        self.name_entry.delete(0, "end")
        self.category_var.set("whitelist")
        self.selected_image_path = None
        
        self.image_label.configure(image=None, text="📷 Chọn ảnh chân dung")
        self.image_info_label.configure(text="Chưa chọn ảnh")
