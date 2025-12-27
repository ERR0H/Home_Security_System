"""
Tab 4: Thống Kê & Lịch Sử
Bảng Treeview lịch sử phát hiện, bộ lọc theo ngày, thống kê
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class StatisticsTab(ctk.CTkFrame):
    """
    Tab thống kê và lịch sử.
    
    Giao diện:
    - Trên: Bộ lọc (theo ngày)
    - Giữa: Bảng treeview lịch sử
    - Dưới: Thống kê tổng hợp
    """
    
    def __init__(self, parent, db_manager):
        """
        Khởi tạo Statistics Tab.
        
        Args:
            parent: Widget cha
            db_manager: DatabaseManager
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        
        # Trạng thái
        self.selected_days = 7
        
        self._setup_ui()
        self._refresh_data()
        
        # Pack frame để fill parent
        self.pack(fill="both", expand=True)
        
        logger.info("StatisticsTab initialized")
    
    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # ==================== BỘ LỌC PHẦN ====================
        filter_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        filter_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(
            filter_frame,
            text="🔍 Bộ Lọc",
            font=("Arial", 13, "bold")
        )
        title.grid(row=0, column=0, padx=10, pady=10)
        
        # Các nút lọc
        button_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        button_frame.grid_columnconfigure((0, 1, 2, 3), weight=0)
        
        today_btn = ctk.CTkButton(
            button_frame,
            text="📅 Hôm Nay",
            command=lambda: self._filter_by_days(1),
            width=100,
            height=35,
            font=("Arial", 10)
        )
        today_btn.grid(row=0, column=0, padx=5)
        
        week_btn = ctk.CTkButton(
            button_frame,
            text="📆 7 Ngày",
            command=lambda: self._filter_by_days(7),
            width=100,
            height=35,
            font=("Arial", 10)
        )
        week_btn.grid(row=0, column=1, padx=5)
        
        month_btn = ctk.CTkButton(
            button_frame,
            text="📊 30 Ngày",
            command=lambda: self._filter_by_days(30),
            width=100,
            height=35,
            font=("Arial", 10)
        )
        month_btn.grid(row=0, column=2, padx=5)
        
        all_btn = ctk.CTkButton(
            button_frame,
            text="📋 Tất Cả",
            command=lambda: self._filter_by_days(999),
            width=100,
            height=35,
            font=("Arial", 10)
        )
        all_btn.grid(row=0, column=3, padx=5)
        
        # Nút refresh
        refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄 Tải Lại",
            command=self._refresh_data,
            width=100,
            height=35,
            font=("Arial", 10)
        )
        refresh_btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")
        
        # ==================== BẢNG LỊCH SỬ ====================
        table_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        title2 = ctk.CTkLabel(
            table_frame,
            text="📊 Lịch Sử Phát Hiện",
            font=("Arial", 13, "bold")
        )
        title2.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Treeview
        tree_frame = ctk.CTkFrame(table_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Tạo Treeview với custom style
        style = ttk.Style()
        style.theme_use("clam")
        
        # Columns
        columns = ("ID", "Thời Gian", "Loại Đối Tượng", "Tên Người", "Camera")
        
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            height=15,
            show="tree headings"
        )
        
        # Định nghĩa heading
        self.tree.column("#0", width=0, stretch="no")
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Thời Gian", width=150, anchor="center")
        self.tree.column("Loại Đối Tượng", width=120, anchor="center")
        self.tree.column("Tên Người", width=150, anchor="center")
        self.tree.column("Camera", width=100, anchor="center")
        
        # Heading
        self.tree.heading("#0", text="", anchor="center")
        self.tree.heading("ID", text="ID", anchor="center")
        self.tree.heading("Thời Gian", text="Thời Gian", anchor="center")
        self.tree.heading("Loại Đối Tượng", text="Loại Đối Tượng", anchor="center")
        self.tree.heading("Tên Người", text="Tên Người", anchor="center")
        self.tree.heading("Camera", text="Camera", anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # ==================== THỐNG KÊ PHẦN ====================
        stats_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        stats_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        title3 = ctk.CTkLabel(
            stats_frame,
            text="📈 Thống Kê Tổng Hợp",
            font=("Arial", 13, "bold")
        )
        title3.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="w")
        
        # Thống kê boxes
        self.total_label = ctk.CTkLabel(stats_frame, text="Tổng Phát Hiện: 0", font=("Arial", 11))
        self.total_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.known_label = ctk.CTkLabel(stats_frame, text="Người Quen: 0", font=("Arial", 11))
        self.known_label.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        self.unknown_label = ctk.CTkLabel(stats_frame, text="Người Lạ: 0", font=("Arial", 11))
        self.unknown_label.grid(row=1, column=2, padx=10, pady=10, sticky="w")
        
        self.suspicious_label = ctk.CTkLabel(stats_frame, text="Tình Nghi: 0", font=("Arial", 11))
        self.suspicious_label.grid(row=1, column=3, padx=10, pady=10, sticky="w")
        
        # Nút xóa dữ liệu
        delete_btn = ctk.CTkButton(
            stats_frame,
            text="🗑️ Xóa Dữ Liệu",
            command=self._show_delete_menu,
            width=120,
            height=35,
            font=("Arial", 10),
            fg_color=("red", "#8B0000"),
            hover_color=("darkred", "#5c0000")
        )
        delete_btn.grid(row=1, column=4, padx=10, pady=10, sticky="e")
    
    def _filter_by_days(self, days: int):
        """Lọc dữ liệu theo số ngày"""
        self.selected_days = days
        self._refresh_data()
    
    def _refresh_data(self):
        """Tải lại dữ liệu từ DB"""
        try:
            # Lấy lịch sử
            history = self.db_manager.get_detection_history(self.selected_days)
            
            # Xóa các item cũ
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Thêm item mới
            for event in history:
                detection_type = event['detection_type']
                
                # Tính màu sắc dựa trên loại
                if detection_type == 'known':
                    tag = 'known'
                elif detection_type == 'unknown':
                    tag = 'unknown'
                else:  # suspicious
                    tag = 'suspicious'
                
                self.tree.insert("", "end", values=(
                    event['id'],
                    event['timestamp'],
                    self._format_detection_type(detection_type),
                    event['user_name'] or 'Ẩn danh',
                    f"Camera {event['camera_id']}"
                ), tags=(tag,))
            
            # Cấu hình tag colors
            self.tree.tag_configure('known', foreground="green")
            self.tree.tag_configure('unknown', foreground="orange")
            self.tree.tag_configure('suspicious', foreground="red")
            
            # Lấy thống kê
            stats = self.db_manager.get_statistics(self.selected_days)
            
            total = stats.get('total_detections', 0)
            counts = stats.get('detection_counts', {})
            
            known_count = counts.get('known', 0)
            unknown_count = counts.get('unknown', 0)
            suspicious_count = counts.get('suspicious', 0)
            
            # Cập nhật labels
            self.total_label.configure(text=f"Tổng Phát Hiện: {total}")
            self.known_label.configure(text=f"Người Quen: {known_count}")
            self.unknown_label.configure(text=f"Người Lạ: {unknown_count}")
            self.suspicious_label.configure(text=f"Tình Nghi: {suspicious_count}")
            
            logger.info(f"Data refreshed: {total} detections in last {self.selected_days} days")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi tải dữ liệu: {str(e)}")
            logger.error(f"Error refreshing data: {e}")
    
    def _show_delete_menu(self):
        """Hiển thị menu xóa dữ liệu"""
        # Tạo cửa sổ xác nhận
        dialog = ctk.CTkToplevel(self)
        dialog.title("🗑️ Xóa Dữ Liệu Lịch Sử")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Tiêu đề
        title = ctk.CTkLabel(
            dialog,
            text="Chọn dữ liệu cần xóa",
            font=("Arial", 13, "bold")
        )
        title.pack(padx=20, pady=15)
        
        # Frame chứa các nút
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Nút xóa hôm nay
        btn_today = ctk.CTkButton(
            button_frame,
            text="📅 Xóa Dữ Liệu Hôm Nay",
            command=lambda: self._delete_and_confirm(1, "hôm nay"),
            height=40,
            font=("Arial", 11),
            fg_color=("orange", "#8B4500")
        )
        btn_today.pack(fill="x", pady=5)
        
        # Nút xóa 7 ngày
        btn_week = ctk.CTkButton(
            button_frame,
            text="📆 Xóa Dữ Liệu 7 Ngày",
            command=lambda: self._delete_and_confirm(7, "7 ngày"),
            height=40,
            font=("Arial", 11),
            fg_color=("orange", "#8B4500")
        )
        btn_week.pack(fill="x", pady=5)
        
        # Nút xóa 30 ngày
        btn_month = ctk.CTkButton(
            button_frame,
            text="📊 Xóa Dữ Liệu 30 Ngày",
            command=lambda: self._delete_and_confirm(30, "30 ngày"),
            height=40,
            font=("Arial", 11),
            fg_color=("orange", "#8B4500")
        )
        btn_month.pack(fill="x", pady=5)
        
        # Nút xóa tất cả
        btn_all = ctk.CTkButton(
            button_frame,
            text="🗑️ Xóa TẤT CẢ Dữ Liệu",
            command=lambda: self._delete_and_confirm(None, "tất cả"),
            height=40,
            font=("Arial", 11, "bold"),
            fg_color=("red", "#8B0000")
        )
        btn_all.pack(fill="x", pady=5)
        
        # Nút đóng
        btn_close = ctk.CTkButton(
            dialog,
            text="Hủy",
            command=dialog.destroy,
            height=35,
            font=("Arial", 10)
        )
        btn_close.pack(padx=20, pady=10, fill="x")
    
    def _delete_and_confirm(self, days, description):
        """Xác nhận và xóa dữ liệu"""
        # Hỏi lại xác nhận
        confirm = messagebox.askyesno(
            "⚠️ Xác Nhận Xóa",
            f"Bạn có chắc muốn xóa dữ liệu {description}?\n\n"
            f"⚠️ Hành động này không thể hoàn tác!"
        )
        
        if confirm:
            try:
                # Xóa dữ liệu
                if days is None:
                    success = self.db_manager.clear_all_detection_history()
                else:
                    success = self.db_manager.delete_detection_history(days=days)
                
                if success:
                    messagebox.showinfo("✅ Thành Công", f"Đã xóa dữ liệu {description} thành công!")
                    self._refresh_data()
                    logger.info(f"Deleted detection history for {description}")
                else:
                    messagebox.showerror("❌ Lỗi", "Không thể xóa dữ liệu. Vui lòng thử lại.")
            
            except Exception as e:
                messagebox.showerror("❌ Lỗi", f"Lỗi khi xóa dữ liệu: {str(e)}")
                logger.error(f"Error deleting detection history: {e}")
    
    def _format_detection_type(self, detection_type: str) -> str:
        """Format loại phát hiện để hiển thị"""
        mapping = {
            'known': '✅ Người Quen',
            'unknown': '👤 Người Lạ',
            'suspicious': '⚠️ Tình Nghi'
        }
        return mapping.get(detection_type, detection_type)

