import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QAction, QMenuBar
from PyQt5.QtGui import QIcon
import logging

from data_migration import DataMigrationApp
from user_guest_creation import UserGuestCreationApp

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SHG Azure Tool")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("path/to/your/icon.png"))  # Update with your icon path
        self.init_ui()

    def init_ui(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        self.button_migration = QPushButton('Azure Tenant Migration Tool', self)
        self.button_migration.setStyleSheet("background-color: #0056b3; color: white;")
        self.button_migration.clicked.connect(self.show_migration_tool)
        self.layout.addWidget(self.button_migration)

        self.button_user_creation = QPushButton('User/Guest Creation Tool', self)
        self.button_user_creation.setStyleSheet("background-color: #0056b3; color: white;")
        self.button_user_creation.clicked.connect(self.show_user_creation_tool)
        self.layout.addWidget(self.button_user_creation)

        self.dark_mode = False  # Default to light mode

        self.init_menu()
        self.set_default_stylesheet()

    def init_menu(self):
        logging.debug('Setting up menu...')
        menubar = self.menuBar()
        options_menu = menubar.addMenu('Options')

        toggle_dark_mode_action = QAction('Toggle Dark Mode', self)
        toggle_dark_mode_action.triggered.connect(self.toggle_dark_mode)
        options_menu.addAction(toggle_dark_mode_action)

        back_to_main_action = QAction('Back to Main', self)
        back_to_main_action.triggered.connect(self.show_main_screen)
        options_menu.addAction(back_to_main_action)

    def set_default_stylesheet(self):
        self.setStyleSheet("")
        self.menuBar().setStyleSheet("""
            QMenuBar {
                background-color: white;
                color: black;
            }
            QMenuBar::item {
                background-color: white;
                color: black;
            }
        """)

    def toggle_dark_mode(self):
        logging.debug('Toggling dark mode...')
        if self.dark_mode:
            self.set_default_stylesheet()
            self.dark_mode = False
        else:
            self.setStyleSheet("background-color: #2c2c2c; color: white;")
            self.menuBar().setStyleSheet("""
                QMenuBar {
                    background-color: #2c2c2c;
                    color: white;
                }
                QMenuBar::item {
                    background-color: #2c2c2c;
                    color: white;
                }
            """)
            self.dark_mode = True

    def show_main_screen(self):
        logging.debug('Showing main screen...')
        self.clear_layout()
        self.layout.addWidget(self.button_migration)
        self.layout.addWidget(self.button_user_creation)

    def show_migration_tool(self):
        logging.debug('Showing migration tool...')
        self.clear_layout()
        self.migration_app = DataMigrationApp()
        self.layout.addWidget(self.migration_app)

    def show_user_creation_tool(self):
        logging.debug('Showing user/guest creation tool...')
        self.clear_layout()
        self.user_creation_app = UserGuestCreationApp(self)
        self.layout.addWidget(self.user_creation_app)

    def clear_layout(self):
        logging.debug('Clearing layout...')
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                logging.debug(f"Removing widget: {widget}")
                widget.setParent(None)
        logging.debug('Layout cleared.')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())
