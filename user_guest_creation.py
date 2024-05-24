import logging
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
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
                self.create_user_in_azure(user_data)
        except Exception as e:
            logging.error(f"Failed to create user: {e}")

    def create_user_in_azure(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Construct the user payload
            user_payload = {
                "accountEnabled": True,
                "displayName": f"{user_data['firstName']} {user_data['lastName']}",
                "mailNickname": f"{user_data['firstName']}.{user_data['lastName']}".lower(),
                "userPrincipalName": f"{user_data['firstName']}.{user_data['lastName']}@yourdomain.com".lower(),
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": True,
                    "password": "TempP@ssword123"  # Temporary password, should be changed
                },
                "department": user_data.get("department", "N/A"),
                "jobTitle": user_data.get("jobTitle", "N/A"),
                "companyName": user_data.get("companyName", "N/A")
            }

            # Create the user in Azure AD
            create_user_url = "https://graph.microsoft.com/v1.0/users"
            response = requests.post(create_user_url, headers=headers, json=user_payload)
            response.raise_for_status()
            logging.info(f"User created: {user_data['firstName']} {user_data['lastName']}")

            # Optionally, add the user to groups based on job title and property
            self.add_user_to_group(user_data)
        except Exception as e:
            logging.error(f"Failed to create user in Azure AD: {e}")

    def add_user_to_group(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Replace with logic to determine the group ID based on job title and property
            group_id = self.get_group_id(user_data)

            # Add user to group
            user_id = self.get_user_id(user_data['userPrincipalName'])
            add_to_group_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
            add_to_group_payload = {
                "@odata.id": f"https://graph.microsoft.com/v1.0/users/{user_id}"
            }
            response = requests.post(add_to_group_url, headers=headers, json=add_to_group_payload)
            response.raise_for_status()
            logging.info(f"User added to group: {user_data['firstName']} {user_data['lastName']}")
        except Exception as e:
            logging.error(f"Failed to add user to group: {e}")

    def get_group_id(self, user_data):
        # Implement logic to get group ID based on user_data['jobTitle'] and other attributes
        # This is a placeholder and should be replaced with actual logic
        return "GROUP_ID"

    def get_user_id(self, user_principal_name):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            return user_info['id']
        except Exception as e:
            logging.error(f"Failed to get user ID: {e}")
            return None

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
