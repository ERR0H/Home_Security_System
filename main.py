import sys
import os

# Thêm thư mục src vào Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Load environment variables từ .env file

if __name__ == "__main__":
    from gui_main import main
    main()
