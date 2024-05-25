import smtplib
from email.mime.text import MIMEText

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QListWidget, QLabel
from azure.identity import InteractiveBrowserCredential
import jwt
import requests
import logging


class UserGuestCreationApp(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.credential = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.tenant_label = QLabel('Tenant: Not Authenticated')
        layout.addWidget(self.tenant_label)

        self.authenticate_button = QPushButton('Authenticate Tenant')
        self.authenticate_button.clicked.connect(self.authenticate_tenant)
        layout.addWidget(self.authenticate_button)

        self.domain_selector = QComboBox()
        layout.addWidget(self.domain_selector)

        self.fetch_groups_button = QPushButton('Fetch Groups')
        self.fetch_groups_button.clicked.connect(self.fetch_groups)
        layout.addWidget(self.fetch_groups_button)

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

    def authenticate_tenant(self):
        try:
            self.credential = InteractiveBrowserCredential()
            token = self.credential.get_token("https://management.azure.com/.default")
            tenant_id = self.extract_tenant_id(token.token)
            self.tenant_label.setText(f'Tenant: {tenant_id}')
            logging.info(f"Authenticated Tenant: {tenant_id}")
        except Exception as e:
            logging.error(f"Failed to authenticate tenant: {e}")

    def extract_tenant_id(self, token):
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded['tid']
        except Exception as e:
            logging.error(f"Failed to extract tenant ID: {e}")
            return None

    def fetch_groups(self):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = "https://graph.microsoft.com/v1.0/groups"
            response = requests.get(url, headers=headers)
            response.raise_for_status()

            # Log the response content for debugging
            logging.debug(f"Response content: {response.content}")

            groups_data = response.json().get('value', [])
            logging.debug(f"Parsed groups data: {groups_data}")
            self.populate_group_selector(groups_data)
        except Exception as e:
            logging.error(f"Failed to fetch groups: {e}")

    def populate_group_selector(self, groups_data):
        self.domain_selector.clear()
        for group in groups_data:
            logging.debug(f"Adding group to selector: {group['displayName']} with ID {group['id']}")
            self.domain_selector.addItem(group['displayName'], group['id'])

    def create_user(self):
        try:
            selected_items = self.user_list.selectedItems()
            if not selected_items:
                logging.info("No user selected.")
                return

            for item in selected_items:
                user_data = item.data(Qt.UserRole)
                self.create_user_in_azure(user_data)
                # Logic for updating ticket and sending email here
        except Exception as e:
            logging.error(f"Failed to create user: {e}")

    def create_user_in_azure(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            user_payload = {
                "accountEnabled": True,
                "displayName": f"{user_data['firstName']} {user_data['lastName']}",
                "mailNickname": f"{user_data['firstName']}.{user_data['lastName']}".lower(),
                "userPrincipalName": f"{user_data['firstName']}.{user_data['lastName']}@yourdomain.com".lower(),
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": True,
                    "password": "TempP@ssword123"
                },
                "department": user_data.get("department", "N/A"),
                "jobTitle": user_data.get("jobTitle", "N/A"),
                "companyName": user_data.get("companyName", "N/A")
            }

            create_user_url = "https://graph.microsoft.com/v1.0/users"
            response = requests.post(create_user_url, headers=headers, json=user_payload)
            response.raise_for_status()
            logging.info(f"User created: {user_data['firstName']} {user_data['lastName']}")

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

            group_id = self.domain_selector.currentData()
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
                self.create_guest_in_azure(user_data)
                # Logic for updating ticket here
        except Exception as e:
            logging.error(f"Failed to create guest: {e}")

    def create_guest_in_azure(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            guest_payload = {
                "invitedUserDisplayName": f"{user_data['firstName']} {user_data['lastName']}",
                "invitedUserEmailAddress": f"{user_data['email']}",
                "inviteRedirectUrl": "https://myapps.microsoft.com",
                "sendInvitationMessage": True
            }

            create_guest_url = "https://graph.microsoft.com/v1.0/invitations"
            response = requests.post(create_guest_url, headers=headers, json=guest_payload)
            response.raise_for_status()
            logging.info(f"Guest created: {user_data['firstName']} {user_data['lastName']}")

            self.add_guest_to_group(user_data)
        except Exception as e:
            logging.error(f"Failed to create guest in Azure AD: {e}")

    def add_guest_to_group(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            group_id = self.domain_selector.currentData()
            guest_user_id = self.get_user_id(user_data['email'])

            if not guest_user_id:
                logging.error(f"Guest user ID not found for {user_data['email']}")
                return

            add_to_group_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
            add_to_group_payload = {
                "@odata.id": f"https://graph.microsoft.com/v1.0/users/{guest_user_id}"
            }
            response = requests.post(add_to_group_url, headers=headers, json=add_to_group_payload)
            response.raise_for_status()
            logging.info(f"Guest added to group: {user_data['firstName']} {user_data['lastName']}")
        except Exception as e:
            logging.error(f"Failed to add guest to group: {e}")

    def send_email(self, user_data, subject, body, to_email):
        try:
            smtp_server = "smtp.office365.com"  # Microsoft 365 SMTP server
            smtp_port = 587  # Microsoft 365 SMTP port
            smtp_username = "yourusername@yourdomain.com"  # Your Microsoft 365 email
            smtp_password = "yourpassword"  # Your Microsoft 365 email password
            from_email = smtp_username  # Same as smtp_username for Microsoft 365

            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())

            logging.info(f"Sent email to {user_data['firstName']} {user_data['lastName']}")
        except Exception as e:
            logging.error(f"Failed to send email: {e}")

    def generate_email_body(self, user_data):
        return f"""
        Dear {user_data['firstName']} {user_data['lastName']},

        Your account has been created successfully. Here are your credentials:

        Username: {user_data['firstName']}.{user_data['lastName']}@yourdomain.com
        Temporary Password: TempP@ssword123

        Please change your password upon first login.

        Regards,
        IT Team
        """
