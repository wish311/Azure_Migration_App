import logging
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
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

        self.fetch_requests_button = QPushButton('Fetch User Requests')
        self.fetch_requests_button.clicked.connect(self.fetch_user_requests)
        layout.addWidget(self.fetch_requests_button)

        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        self.create_user_button = QPushButton('Create User')
        self.create_user_button.clicked.connect(self.create_user)
        layout.addWidget(self.create_user_button)

        self.create_guest_button = QPushButton('Create Guest')
        self.create_guest_button.clicked.connect(self.create_guest)
        layout.addWidget(self.create_guest_button)

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

    def fetch_user_requests(self):
        try:
            api_url = "https://api.solarwinds.com/v1/requests"  # Example API URL, replace with actual
            api_token = "YOUR_SOLARWINDS_API_TOKEN"  # Replace with your API token
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            requests_data = response.json()
            self.populate_user_list(requests_data)
        except Exception as e:
            logging.error(f"Failed to fetch user requests: {e}")

    def populate_user_list(self, requests_data):
        self.user_list.clear()
        for request in requests_data:
            user_info = f"{request['firstName']} {request['lastName']} ({request['email']})"
            item = QListWidgetItem(user_info)
            item.setData(Qt.UserRole, request)
            self.user_list.addItem(item)

    def create_user(self):
        try:
            selected_items = self.user_list.selectedItems()
            if not selected_items:
                logging.info("No user selected.")
                return

            for item in selected_items:
                user_data = item.data(Qt.UserRole)
                # Implement user creation logic here using user_data
                logging.info(f"Creating user: {user_data['firstName']} {user_data['lastName']}")
        except Exception as e:
            logging.error(f"Failed to create user: {e}")

    def create_guest(self):
        try:
            selected_items = self.user_list.selectedItems()
            if not selected_items:
                logging.info("No guest selected.")
                return

            for item in selected_items:
                user_data = item.data(Qt.UserRole)
                # Implement guest creation logic here using user_data
                logging.info(f"Creating guest: {user_data['firstName']} {user_data['lastName']}")
        except Exception as e:
            logging.error(f"Failed to create guest: {e}")
