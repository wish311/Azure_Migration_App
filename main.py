import sys
from PyQt5.QtWidgets import QApplication
from ui_design import MainApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = MainApp()
    sys.exit(app.exec_())
