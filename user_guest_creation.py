import logging
import smtplib
from email.mime.text import MIMEText

import jwt
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel,
    QListWidgetItem, QLineEdit, QFormLayout, QDialog,
    QDialogButtonBox
)
from azure.identity import InteractiveBrowserCredential

import config


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

        self.groups_label = QLabel('Groups:')
        layout.addWidget(self.groups_label)

        self.groups_list = QListWidget()
        self.groups_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.groups_list)

        self.fetch_groups_button = QPushButton('Fetch Groups')
        self.fetch_groups_button.clicked.connect(self.fetch_groups)
        layout.addWidget(self.fetch_groups_button)

        self.user_list = QListWidget()
        layout.addWidget(self.user_list)

        self.fetch_tickets_button = QPushButton('Fetch Tickets')
        self.fetch_tickets_button.clicked.connect(self.fetch_tickets)
        layout.addWidget(self.fetch_tickets_button)

        self.create_user_button = QPushButton('Create User')
        self.create_user_button.clicked.connect(self.create_user)
        layout.addWidget(self.create_user_button)

        self.create_guest_button = QPushButton('Create Guest')
        self.create_guest_button.clicked.connect(self.create_guest)
        layout.addWidget(self.create_guest_button)

        self.manual_user_button = QPushButton('Create User Manually')
        self.manual_user_button.clicked.connect(self.show_manual_user_dialog)
        layout.addWidget(self.manual_user_button)

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

            groups_data = response.json().get('value', [])
            self.populate_group_selector(groups_data)
        except Exception as e:
            logging.error(f"Failed to fetch groups: {e}")

    def populate_group_selector(self, groups_data):
        self.groups_list.clear()
        for group in groups_data:
            item = QListWidgetItem(group['displayName'])
            item.setData(Qt.UserRole, group['id'])
            item.setCheckState(Qt.Unchecked)
            self.groups_list.addItem(item)

    def fetch_tickets(self):
        try:
            api_url = "https://your_solarwinds_api_endpoint"  # Replace with your SolarWinds API endpoint
            api_key = "your_api_key"  # Replace with your API key
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            tickets = response.json()
            self.populate_user_list(tickets)
        except Exception as e:
            logging.error(f"Failed to fetch tickets: {e}")

    def populate_user_list(self, tickets):
        self.user_list.clear()
        for ticket in tickets:
            item_text = f"{ticket['name']} - {ticket['requester']['name']} ({ticket['requester']['email']})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ticket)
            self.user_list.addItem(item)

    def create_user(self):
        try:
            selected_items = self.user_list.selectedItems()
            if not selected_items:
                logging.info("No user selected.")
                return

            for item in selected_items:
                ticket = item.data(Qt.UserRole)
                user_data = {
                    "firstName": ticket['requester']['name'].split()[0],
                    "lastName": ticket['requester']['name'].split()[-1],
                    "email": f"{ticket['requester']['name'].split()[0].lower()}.{ticket['requester']['name'].split()[-1].lower()}@yourdomain.com",
                    "department": ticket['department']['name'],
                    "jobTitle": ticket['assignee']['name'],
                    "companyName": ticket['site']['name'],
                    "empID": ticket.get('custom_fields_values', {}).get('empID', 'N/A')
                }
                self.create_user_in_azure(user_data)
                self.update_ticket_status(ticket['id'])
                self.send_email(user_data, "User Account Created", self.generate_email_body(user_data),
                                ticket['assignee']['email'])
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
                "companyName": user_data.get("companyName", "N/A"),
                "employeeId": user_data.get("empID", "N/A")
            }

            logging.debug(f"User payload: {user_payload}")

            create_user_url = "https://graph.microsoft.com/v1.0/users"
            response = requests.post(create_user_url, headers=headers, json=user_payload)
            response.raise_for_status()
            logging.info(f"User created: {user_data['firstName']} {user_data['lastName']}")

            self.add_user_to_groups(user_data)
        except Exception as e:
            logging.error(f"Failed to create user in Azure AD: {e}")

    def add_user_to_groups(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            user_id = self.get_user_id(user_data['userPrincipalName'])
            selected_groups = [self.groups_list.item(i).data(Qt.UserRole) for i in range(self.groups_list.count()) if
                               self.groups_list.item(i).checkState() == Qt.Checked]

            for group_id in selected_groups:
                add_to_group_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
                add_to_group_payload = {
                    "@odata.id": f"https://graph.microsoft.com/v1.0/users/{user_id}"
                }
                response = requests.post(add_to_group_url, headers=headers, json=add_to_group_payload)
                response.raise_for_status()
                logging.info(f"User added to group: {group_id}")

        except Exception as e:
            logging.error(f"Failed to add user to groups: {e}")

    def get_user_id(self, user_principal_name):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}"
            }
            url = f"https://graph.microsoft.com/v1.0/users/{user_principal_name}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()
            return user_data['id']
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
                ticket = item.data(Qt.UserRole)
                user_data = {
                    "firstName": ticket['requester']['name'].split()[0],
                    "lastName": ticket['requester']['name'].split()[-1],
                    "email": ticket['requester']['email']
                }
                self.create_guest_in_azure(user_data)
                self.update_ticket_status(ticket['id'])
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

            self.add_guest_to_groups(user_data)
        except Exception as e:
            logging.error(f"Failed to create guest in Azure AD: {e}")

    def add_guest_to_groups(self, user_data):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            guest_user_id = self.get_user_id(user_data['email'])

            if not guest_user_id:
                logging.error(f"Guest user ID not found for {user_data['email']}")
                return

            selected_groups = [self.groups_list.item(i).data(Qt.UserRole) for i in range(self.groups_list.count()) if
                               self.groups_list.item(i).checkState() == Qt.Checked]

            for group_id in selected_groups:
                add_to_group_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"
                add_to_group_payload = {
                    "@odata.id": f"https://graph.microsoft.com/v1.0/users/{guest_user_id}"
                }
                response = requests.post(add_to_group_url, headers=headers, json=add_to_group_payload)
                response.raise_for_status()
                logging.info(f"Guest added to group: {group_id}")

        except Exception as e:
            logging.error(f"Failed to add guest to groups: {e}")

    def update_ticket_status(self, ticket_id):
        try:
            api_url = f"https://your_solarwinds_api_endpoint/{ticket_id}"  # Replace with your SolarWinds API endpoint
            api_key = "your_api_key"  # Replace with your API key
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            update_data = {
                "state": "Resolved",
                "resolution_code": "Done",
                "resolution_description": "User/Guest account created successfully."
            }
            response = requests.put(api_url, headers=headers, json=update_data)
            response.raise_for_status()
            logging.info(f"Ticket {ticket_id} updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update ticket status: {e}")

    def send_email(self, user_data, subject, body, to_email):
        try:
            smtp_server = config.SMTP_SERVER
            smtp_port = config.SMTP_PORT
            smtp_username = config.SMTP_USERNAME
            smtp_password = config.SMTP_PASSWORD
            from_email = smtp_username  # Same as smtp_username for Microsoft 365

            if not smtp_username or not smtp_password:
                logging.error("SMTP credentials are not set in environment variables.")
                return

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

    def show_manual_user_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Create User Manually')

        form_layout = QFormLayout()
        first_name_input = QLineEdit()
        last_name_input = QLineEdit()
        email_input = QLineEdit()
        department_input = QLineEdit()
        job_title_input = QLineEdit()
        company_name_input = QLineEdit()
        emp_id_input = QLineEdit()
        manager_email_input = QLineEdit()

        form_layout.addRow('First Name:', first_name_input)
        form_layout.addRow('Last Name:', last_name_input)
        form_layout.addRow('Email:', email_input)
        form_layout.addRow('Department:', department_input)
        form_layout.addRow('Job Title:', job_title_input)
        form_layout.addRow('Company Name:', company_name_input)
        form_layout.addRow('EMP ID:', emp_id_input)
        form_layout.addRow('Manager Email:', manager_email_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(lambda: self.create_manual_user(
            first_name_input.text(),
            last_name_input.text(),
            email_input.text(),
            department_input.text(),
            job_title_input.text(),
            company_name_input.text(),
            emp_id_input.text(),
            manager_email_input.text(),
            dialog
        ))
        buttons.rejected.connect(dialog.reject)

        form_layout.addWidget(buttons)
        dialog.setLayout(form_layout)
        dialog.exec_()

    def create_manual_user(self, first_name, last_name, email, department, job_title, company_name, emp_id,
                           manager_email, dialog):
        try:
            email = f"{first_name.lower()}.{last_name.lower()}@yourdomain.com"
            mail_nickname = f"{first_name.lower()}.{last_name.lower()}"
            user_data = {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "mailNickname": mail_nickname,
                "department": department,
                "jobTitle": job_title,
                "companyName": company_name,
                "empID": emp_id
            }
            self.create_user_in_azure(user_data)
            self.send_email(user_data, "User Account Created", self.generate_email_body(user_data), manager_email)
            dialog.accept()
        except Exception as e:
            logging.error(f"Failed to create manual user: {e}")
            dialog.reject()
