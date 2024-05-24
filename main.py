import sys

from PyQt5.QtWidgets import QApplication

from ui_design import MigrationApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MigrationApp()
    sys.exit(app.exec_())
