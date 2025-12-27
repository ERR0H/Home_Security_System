"""
Module GUI chính sử dụng customtkinter
Cấu trúc ứng dụng với 6 tab: Monitor, Monitor Grid, Camera Setup, Face Database, Statistics, Info
"""
import sys
import os
import customtkinter as ctk
from PIL import Image
import logging

# Thêm src vào path để import các module khác
sys.path.insert(0, os.path.dirname(__file__))

from database import DatabaseManager
from face_recognizer import FaceRecognizer
from camera_handler import CameraManager

# Import các tab GUI
from gui_monitor import MonitorTab
from gui_monitor_grid import MonitorGridTab
from gui_camera_setup import CameraSetupTab
from gui_face_db import FaceDBTab
from gui_statistics import StatisticsTab
from gui_info import InfoTab

logger = logging.getLogger(__name__)


class MainApp(ctk.CTk):
    """
    Ứng dụng GUI chính.
    
    Cấu trúc:
    - Tab 1: Monitor Center (Giám sát 1 camera chi tiết)
    - Tab 2: Monitor Grid (Giám sát nhiều camera - Grid 2x2)
    - Tab 3: Camera Setup (Quản lý camera)
    - Tab 4: Face Database (Quản lý khuôn mặt)
    - Tab 5: Statistics (Thống kê & Lịch sử)
    - Tab 6: Info (Thông tin ứng dụng)
    """
    
    def __init__(self):
        """Khởi tạo ứng dụng chính"""
        super().__init__()
        
        # Cấu hình cửa sổ
        self.title("Hệ Thống Giám Sát An Ninh Hộ Gia Đình")
        self.geometry("1400x900")
        
        # Giao diện Dark Mode mặc định
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Icon (tuỳ chọn)
        try:
            self.iconbitmap("assets/icon.ico")
        except:
            pass  # Không có icon thì bỏ qua
        
        # Khởi tạo các manager
        self.db_manager = DatabaseManager()
        self.face_recognizer = FaceRecognizer(self.db_manager)
        self.camera_manager = CameraManager(self.db_manager)
        
        logger.info("Managers initialized")
        
        # Khởi tạo GUI
        self._setup_ui()
        
        # Xử lý đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("MainApp initialized successfully")
    
    def _setup_ui(self):
        """Thiết lập giao diện chính"""
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(side="top", fill="both", expand=True, padx=0, pady=0)
        
        # Header bar
        header = ctk.CTkFrame(main_container, fg_color=("gray90", "gray20"))
        header.pack(side="top", fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            header,
            text="🔒 HỆ THỐNG GIÁM SÁT AN NINH HỘ GIA ĐÌNH",
            font=("Arial", 16, "bold"),
            text_color=("black", "white")
        )
        title_label.pack(side="left", padx=10, pady=5)
        
        # Tabview
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tạo các tab
        tab_monitor = self.tabview.add("📹 Giám Sát")
        tab_monitor_grid = self.tabview.add("📺 Giám Sát Toàn Cảnh")
        tab_camera_setup = self.tabview.add("📷 Cài Đặt Camera")
        tab_face_db = self.tabview.add("👤 Quản Lý Khuôn Mặt")
        tab_statistics = self.tabview.add("📊 Thống Kê")
        tab_info = self.tabview.add("ℹ️ Thông Tin")
        
        # Khởi tạo các Tab GUI
        self.monitor_tab = MonitorTab(
            tab_monitor,
            self.db_manager,
            self.face_recognizer,
            self.camera_manager
        )
        
        self.monitor_grid_tab = MonitorGridTab(
            tab_monitor_grid,
            self.db_manager,
            self.face_recognizer,
            self.camera_manager
        )
        
        self.camera_setup_tab = CameraSetupTab(
            tab_camera_setup,
            self.db_manager,
            self.camera_manager
        )
        
        self.face_db_tab = FaceDBTab(
            tab_face_db,
            self.db_manager,
            self.face_recognizer
        )
        
        self.statistics_tab = StatisticsTab(
            tab_statistics,
            self.db_manager
        )
        
        self.info_tab = InfoTab(tab_info)        
        
        logger.info("UI setup completed")
    
    def update_status(self, message: str):
        """Cập nhật status bar"""
        self.status_label.configure(text=message)
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        logger.info("Closing application...")
        
        try:
            # Dừng tất cả camera
            if hasattr(self, 'camera_manager'):
                self.camera_manager.stop_all()
            
            # Đóng database
            if hasattr(self, 'db_manager'):
                self.db_manager.close()
            
            # Đóng các tab
            if hasattr(self, 'monitor_tab'):
                self.monitor_tab.cleanup()
            
            if hasattr(self, 'monitor_grid_tab'):
                self.monitor_grid_tab.cleanup()
            
            logger.info("Application closed successfully")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        finally:
            self.destroy()


def main():
    """Hàm main để khởi chạy ứng dụng"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = MainApp()
    app.mainloop()


if __name__ == "__main__":
    main()
