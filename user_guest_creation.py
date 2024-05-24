import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QCheckBox
from azure.identity import InteractiveBrowserCredential
import jwt

class UserGuestCreationApp(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.credential = None
        self.tenant_id = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.auth_button = QPushButton('Sign in to Tenant')
        self.auth_button.clicked.connect(self.authenticate_tenant)
        layout.addWidget(self.auth_button)

        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        self.create_user_button = QPushButton('Create User')
        self.create_user_button.clicked.connect(self.create_user)
        layout.addWidget(self.create_user_button)

        self.create_guest_button = QPushButton('Create Guest')
        self.create_guest_button.clicked.connect(self.create_guest)
        layout.addWidget(self.create_guest_button)

        self.dark_mode_checkbox = QCheckBox('Dark Mode')
        self.dark_mode_checkbox.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)

        self.setLayout(layout)
        self.setWindowTitle('User/Guest Creation Tool')

    def toggle_dark_mode(self):
        self.parent.toggle_dark_mode()

    def authenticate_tenant(self):
        try:
            self.credential = InteractiveBrowserCredential()
            token = self.credential.get_token("https://management.azure.com/.default")
            self.tenant_id = self.extract_tenant_id(token.token)
            logging.info("Authenticated Tenant")
        except Exception as e:
            logging.error(f"Failed to authenticate tenant: {e}")

    def extract_tenant_id(self, token):
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded['tid']
        except Exception as e:
            logging.error(f"Failed to extract tenant ID: {e}")
            return None

    def create_user(self):
        try:
            # Implement user creation logic here
            logging.info("Creating user...")
        except Exception as e:
            logging.error(f"Failed to create user: {e}")

    def create_guest(self):
        try:
            # Implement guest creation logic here
            logging.info("Creating guest...")
        except Exception as e:
            logging.error(f"Failed to create guest: {e}")
