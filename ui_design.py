import sys
import logging
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QApplication, QCheckBox, QTextEdit, QListWidgetItem, QComboBox
from PyQt5.QtCore import Qt
from azure.identity import InteractiveBrowserCredential
import jwt
from data_migration import DataMigration

# Configure logging
logging.basicConfig(level=logging.INFO)

class AuthenticationModule(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.auth_button_source = QPushButton('Sign in to Source Tenant')
        self.auth_button_source.clicked.connect(self.parent.authenticate_source_tenant)
        layout.addWidget(self.auth_button_source)

        self.auth_button_destination = QPushButton('Sign in to Destination Tenant')
        self.auth_button_destination.clicked.connect(self.parent.authenticate_destination_tenant)
        layout.addWidget(self.auth_button_destination)

        self.setLayout(layout)


class DataListingModule(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.data_list = QListWidget()
        self.data_list.addItems(['Users', 'Groups', 'Files'])
        self.data_list.itemClicked.connect(self.parent.list_data)
        layout.addWidget(self.data_list)

        self.item_list = QListWidget()
        layout.addWidget(self.item_list)

        self.setLayout(layout)


class DomainSelectorModule(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.domain_selector = QComboBox()
        layout.addWidget(self.domain_selector)

        self.data_display = QTextEdit()
        self.data_display.setReadOnly(True)
        layout.addWidget(self.data_display)

        self.setLayout(layout)


class MigrationActionsModule(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.migrate_button = QPushButton('Migrate Selected Users or Groups')
        self.migrate_button.clicked.connect(self.parent.migrate_selected_items)
        layout.addWidget(self.migrate_button)

        self.delete_checkbox = QCheckBox('Delete Users from Source Tenant After Migration')
        layout.addWidget(self.delete_checkbox)

        self.dark_mode_checkbox = QCheckBox('Dark Mode')
        self.dark_mode_checkbox.stateChanged.connect(self.parent.toggle_dark_mode)
        layout.addWidget(self.dark_mode_checkbox)

        self.setLayout(layout)


class MigrationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.source_credential = None
        self.target_credential = None
        self.source_tenant_id = None
        self.target_tenant_id = None
        self.verified_domains = []
        self.data_migration = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.auth_module = AuthenticationModule(self)
        layout.addWidget(self.auth_module)

        self.data_listing_module = DataListingModule(self)
        layout.addWidget(self.data_listing_module)

        self.domain_selector_module = DomainSelectorModule(self)
        layout.addWidget(self.domain_selector_module)

        self.migration_actions_module = MigrationActionsModule(self)
        layout.addWidget(self.migration_actions_module)

        self.setLayout(layout)
        self.setWindowTitle('Azure Tenant Migration')
        self.set_default_stylesheet()
        self.show()

    def set_default_stylesheet(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

    def set_dark_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: white;
            }
            QPushButton {
                background-color: #444;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QListWidget {
                background-color: #3e3e3e;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QTextEdit {
                background-color: #3e3e3e;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)

    def toggle_dark_mode(self):
        if self.migration_actions_module.dark_mode_checkbox.isChecked():
            self.set_dark_stylesheet()
        else:
            self.set_default_stylesheet()

    def authenticate_source_tenant(self):
        try:
            self.source_credential = InteractiveBrowserCredential()
            token = self.source_credential.get_token("https://management.azure.com/.default")
            self.source_tenant_id = self.extract_tenant_id(token.token)
            logging.info("Authenticated Source Tenant")
            self.domain_selector_module.data_display.append("Authenticated Source Tenant")
        except Exception as e:
            logging.error(f"Failed to authenticate source tenant: {e}")
            self.domain_selector_module.data_display.append(f"Failed to authenticate source tenant: {e}")

    def authenticate_destination_tenant(self):
        try:
            self.target_credential = InteractiveBrowserCredential()
            token = self.target_credential.get_token("https://management.azure.com/.default")
            self.target_tenant_id = self.extract_tenant_id(token.token)
            self.verified_domains = self.get_verified_domains()
            self.domain_selector_module.domain_selector.clear()
            self.domain_selector_module.domain_selector.addItems(self.verified_domains)
            logging.info("Authenticated Destination Tenant")
            self.domain_selector_module.data_display.append("Authenticated Destination Tenant")
        except Exception as e:
            logging.error(f"Failed to authenticate destination tenant: {e}")
            self.domain_selector_module.data_display.append(f"Failed to authenticate destination tenant: {e}")

    def extract_tenant_id(self, token):
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded['tid']
        except Exception as e:
            logging.error(f"Failed to extract tenant ID: {e}")
            return None

    def get_verified_domains(self):
        try:
            token = self.target_credential.get_token("https://graph.microsoft.com/.default").token
            url = 'https://graph.microsoft.com/v1.0/domains'
            response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
            response.raise_for_status()
            domains = response.json().get('value', [])
            return [domain['id'] for domain in domains]  # Return list of domain IDs
        except Exception as e:
            logging.error(f"Failed to get verified domains: {e}")
            self.domain_selector_module.data_display.append(f"Failed to get verified domains: {e}")
            return []

    def list_data(self, item):
        try:
            if not self.source_credential or not self.source_tenant_id:
                self.domain_selector_module.data_display.append("Please authenticate the source tenant first.")
                return

            data_type = item.text()
            if data_type == 'Users':
                self.list_users()
            elif data_type == 'Groups':
                self.list_groups()
            else:
                self.domain_selector_module.data_display.append(f"Listing of {data_type} is not yet implemented.")
        except Exception as e:
            logging.error(f"Failed to list data for source tenant: {e}")
            self.domain_selector_module.data_display.append(f"Failed to list data for source tenant: {e}")

    def list_users(self):
        try:
            self.data_listing_module.item_list.clear()
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None, self.source_credential, None)
            users = self.data_migration.get_users()
            if users:
                for user in users:
                    item = QListWidgetItem(f"{user.get('displayName', 'N/A')} ({user.get('userPrincipalName', 'N/A')})")
                    item.setData(Qt.UserRole, user)
                    self.data_listing_module.item_list.addItem(item)
            else:
                self.domain_selector_module.data_display.append("No users found.")
        except Exception as e:
            logging.error(f"Failed to list users: {e}")
            self.domain_selector_module.data_display.append(f"Failed to list users: {e}")

    def list_groups(self):
        try:
            self.data_listing_module.item_list.clear()
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None, self.source_credential, None)
            groups = self.data_migration.get_groups()
            if groups:
                for group in groups:
                    item = QListWidgetItem(f"{group.get('displayName', 'N/A')} ({group.get('id', 'N/A')})")
                    item.setData(Qt.UserRole, group)
                    self.data_listing_module.item_list.addItem(item)
            else:
                self.domain_selector_module.data_display.append("No groups found.")
        except Exception as e:
            logging.error(f"Failed to list groups: {e}")
            self.domain_selector_module.data_display.append(f"Failed to list groups: {e}")

    def migrate_selected_items(self):
        try:
            selected_items = self.data_listing_module.item_list.selectedItems()
            if not selected_items:
                self.domain_selector_module.data_display.append("Please select users or groups to migrate.")
                return

            selected_domain = self.domain_selector_module.domain_selector.currentText()
            if not selected_domain:
                self.domain_selector_module.data_display.append("Please select a target domain.")
                return

            items_to_migrate = [item.data(Qt.UserRole) for item in selected_items]
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None, self.target_credential, selected_domain)
            for item in items_to_migrate:
                if 'userPrincipalName' in item:
                    created_user = self.data_migration.migrate_user(item)
                    if created_user:
                        self.domain_selector_module.data_display.append(f"Migrated user: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                        if self.migration_actions_module.delete_checkbox.isChecked():
                            self.data_migration.remove_user(item['id'])
                            self.domain_selector_module.data_display.append(f"Removed user from source tenant: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                        self.data_listing_module.item_list.takeItem(self.data_listing_module.item_list.row(selected_items.pop(0)))
                    else:
                        self.domain_selector_module.data_display.append(f"Failed to migrate user: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                elif 'mailNickname' in item:
                    created_group = self.data_migration.migrate_group(item)
                    if created_group:
                        self.domain_selector_module.data_display.append(f"Migrated group: {item.get('displayName', 'N/A')} ({item.get('id', 'N/A')})")
                        self.data_listing_module.item_list.takeItem(self.data_listing_module.item_list.row(selected_items.pop(0)))
                    else:
                        self.domain_selector_module.data_display.append(f"Failed to migrate group: {item.get('displayName', 'N/A')} ({item.get('id', 'N/A')})")
        except Exception as e:
            logging.error(f"Failed to migrate items: {e}")
            self.domain_selector_module.data_display.append(f"Failed to migrate items: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MigrationApp()
    sys.exit(app.exec_())
