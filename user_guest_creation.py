from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QListWidget, QCheckBox, QComboBox, QApplication
import logging
import random
import string
from azure.identity import InteractiveBrowserCredential
import requests
import sys

class UserGuestCreationApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.credential = None
        self.init_ui()

    def init_ui(self):
        logging.debug("Initializing UserGuestCreationApp UI...")
        layout = QVBoxLayout()

        self.tenant_label = QLabel("Tenant: Not Authenticated", self)
        layout.addWidget(self.tenant_label)

        self.authenticate_button = QPushButton("Authenticate Tenant", self)
        self.authenticate_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.authenticate_button.clicked.connect(self.authenticate_tenant)
        layout.addWidget(self.authenticate_button)

        self.groups_label = QLabel("Select Groups", self)
        layout.addWidget(self.groups_label)

        self.groups_list = QListWidget(self)
        layout.addWidget(self.groups_list)

        self.fetch_groups_button = QPushButton("Fetch Groups", self)
        self.fetch_groups_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.fetch_groups_button.clicked.connect(self.fetch_groups)
        layout.addWidget(self.fetch_groups_button)

        self.user_list = QListWidget(self)
        layout.addWidget(self.user_list)

        self.create_user_button = QPushButton("Create User", self)
        self.create_user_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.create_user_button.clicked.connect(self.create_user)
        layout.addWidget(self.create_user_button)

        self.create_guest_button = QPushButton("Create Guest", self)
        self.create_guest_button.setStyleSheet("background-color: #0056b3; color: white;")
        self.create_guest_button.clicked.connect(self.create_guest)
        layout.addWidget(self.create_guest_button)

        self.setLayout(layout)

    def authenticate_tenant(self):
        logging.debug("Authenticating tenant...")
        try:
            self.credential = InteractiveBrowserCredential()
            token = self.credential.get_token("https://graph.microsoft.com/.default")
            self.headers = {
                'Authorization': f'Bearer {token.token}',
                'Content-Type': 'application/json'
            }
            self.tenant_label.setText("Tenant: Authenticated")
            logging.info("Authenticated Tenant")
        except Exception as e:
            logging.error(f"Failed to authenticate tenant: {e}")
            self.tenant_label.setText("Tenant: Not Authenticated")

    def fetch_groups(self):
        logging.debug("Fetching groups...")
        if not self.credential:
            logging.error("Tenant not authenticated.")
            return
        try:
            response = requests.get('https://graph.microsoft.com/v1.0/groups', headers=self.headers)
            response.raise_for_status()
            groups = response.json().get('value', [])
            self.groups_list.clear()
            for group in groups:
                self.groups_list.addItem(group['displayName'])
            logging.info("Fetched groups successfully.")
        except Exception as e:
            logging.error(f"Failed to fetch groups: {e}")

    def generate_random_password(self, length=8):
        letters = string.ascii_letters
        digits = string.digits
        password = ''.join(random.choice(letters + digits) for i in range(length))
        return password

    def create_user(self):
        logging.debug("Creating user...")
        try:
            user_data = {
                'accountEnabled': True,
                'displayName': 'John Doe',
                'mailNickname': 'john.doe',
                'userPrincipalName': 'john.doe@yourdomain.com',
                'passwordProfile': {
                    'forceChangePasswordNextSignIn': True,
                    'password': self.generate_random_password()
                },
                'department': 'IT',
                'jobTitle': 'Developer',
                'companyName': 'Example Corp',
                'employeeId': '123456'
            }
            logging.debug(f"User payload: {user_data}")
            response = requests.post('https://graph.microsoft.com/v1.0/users', headers=self.headers, json=user_data)
            response.raise_for_status()
            logging.info("User created successfully.")
            self.send_email(user_data, "Account Created", "Your account has been created.", "manager@example.com")
        except Exception as e:
            logging.error(f"Failed to create user: {e}")

    def create_guest(self):
        logging.debug("Creating guest...")
        try:
            user_data = {
                'accountEnabled': True,
                'displayName': 'Guest User',
                'mailNickname': 'guest.user',
                'userPrincipalName': 'guest.user@yourdomain.com',
                'passwordProfile': {
                    'forceChangePasswordNextSignIn': True,
                    'password': self.generate_random_password()
                },
                'department': 'Guest',
                'jobTitle': 'Guest',
                'companyName': 'Example Corp',
                'employeeId': '654321'
            }
            logging.debug(f"Guest payload: {user_data}")
            response = requests.post('https://graph.microsoft.com/v1.0/users', headers=self.headers, json=user_data)
            response.raise_for_status()
            logging.info("Guest created successfully.")
            self.send_email(user_data, "Guest Account Created", "Your guest account has been created.", "manager@example.com")
        except Exception as e:
            logging.error(f"Failed to create guest: {e}")

    def send_email(self, user_data, subject, body, to_email):
        logging.debug(f"Generating email for {user_data['userPrincipalName']}")
        try:
            smtp_server = "smtp.office365.com"  # Microsoft 365 SMTP server
            smtp_port = 587  # Microsoft 365 SMTP port
            smtp_username = "yourusername@yourdomain.com"  # Your Microsoft 365 email
            smtp_password = "yourpassword"  # Your Microsoft 365 email password
            from_email = smtp_username  # Same as smtp_username for Microsoft 365

            msg = f"Subject: {subject}\n\n{body}\n\nUsername: {user_data['userPrincipalName']}\nPassword: {user_data['passwordProfile']['password']}"
            logging.debug(f"Email content: {msg}")
            print(msg)  # Temporarily print the email instead of sending
            logging.info(f"Generated email for {user_data['userPrincipalName']}")
        except Exception as e:
            logging.error(f"Failed to generate email: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication([])
    window = UserGuestCreationApp()
    window.show()
    sys.exit(app.exec_())
