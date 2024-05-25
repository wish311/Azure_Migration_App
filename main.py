import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui_design import MainApp

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("app.log"),
    logging.StreamHandler()
])

def main():
    logging.info('Starting application...')
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    logging.info('Application started.')
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
