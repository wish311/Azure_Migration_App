import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QVBoxLayout, QWidget, QLabel, QPushButton, QStackedWidget
from PyQt5.QtGui import QIcon
from user_guest_creation import UserGuestCreationApp
from data_migration import DataMigrationApp

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.debug('Initializing MainApp...')
        self.init_ui()

    def init_ui(self):
        logging.debug('Setting up UI...')
        self.setWindowTitle('SHG Azure Tool')
        self.setWindowIcon(QIcon('company_icon.png'))  # Ensure the icon file is in the same directory

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.stacked_layout = QStackedWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.addWidget(self.stacked_layout)
        self.main_screen = self.create_main_screen()
        self.stacked_layout.addWidget(self.main_screen)

        self.migration_app = DataMigrationApp(self)
        self.stacked_layout.addWidget(self.migration_app)

        self.user_creation_app = UserGuestCreationApp(self)
        self.stacked_layout.addWidget(self.user_creation_app)

        self.stacked_layout.setCurrentWidget(self.main_screen)

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

    def toggle_dark_mode(self):
        logging.debug('Toggling dark mode...')
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.set_dark_mode_stylesheet()
        else:
            self.set_default_stylesheet()

    def set_default_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
                color: #000000;
            }
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: 1px solid #005bb5;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QLabel {
                color: #000000;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #000000;
            }
            QMenuBar::item {
                background-color: #ffffff;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
        """)

    def set_dark_mode_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2e2e2e;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: 1px solid #005bb5;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QLabel {
                color: #ffffff;
            }
            QMenuBar {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QMenuBar::item {
                background-color: #3a3a3a;
                color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #4a4a4a;
            }
        """)

    def show_main_screen(self):
        logging.debug('Showing main screen...')
        self.stacked_layout.setCurrentWidget(self.main_screen)

    def show_migration_tool(self):
        logging.debug('Showing migration tool...')
        self.stacked_layout.setCurrentWidget(self.migration_app)

    def show_user_creation_tool(self):
        logging.debug('Showing user creation tool...')
        self.stacked_layout.setCurrentWidget(self.user_creation_app)

    def create_main_screen(self):
        main_screen = QWidget()
        layout = QVBoxLayout(main_screen)

        button_migration = QPushButton('Azure Tenant Migration Tool', self)
        button_migration.clicked.connect(self.show_migration_tool)
        layout.addWidget(button_migration)

        button_user_creation = QPushButton('User/Guest Creation Tool', self)
        button_user_creation.clicked.connect(self.show_user_creation_tool)
        layout.addWidget(button_user_creation)

        return main_screen

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ])
    logging.info('Starting application...')
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    logging.info('Application started.')
    sys.exit(app.exec_())
