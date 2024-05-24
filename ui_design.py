import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QStackedWidget, QListWidgetItem, QCheckBox, QListWidget, \
    QComboBox, QTextEdit, QMenuBar, QMenu, QAction
from PyQt5.QtCore import Qt
from azure.identity import InteractiveBrowserCredential
import jwt
import requests
from authentication import AuthenticationModule
from data_selection import DataListingModule, DomainSelectorModule, MigrationActionsModule
from data_migration import DataMigration
from user_guest_creation import UserGuestCreationApp

# Configure logging
logging.basicConfig(level=logging.INFO)


class MainApp(QWidget):
    def __init__(self):
        super().__init__()
        self.dark_mode_enabled = False
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.options_menu = QMenu("Options", self)
        self.toggle_dark_mode_action = QAction("Toggle Dark Mode", self)
        self.toggle_dark_mode_action.triggered.connect(self.toggle_dark_mode)
        self.options_menu.addAction(self.toggle_dark_mode_action)
        self.menu_bar.addMenu(self.options_menu)
        layout.setMenuBar(self.menu_bar)

        self.stack = QStackedWidget(self)

        self.migration_app = MigrationApp(self)
        self.user_guest_creation_app = UserGuestCreationApp(self)

        self.main_screen = QWidget()
        main_screen_layout = QVBoxLayout()
        self.migration_button = QPushButton('Azure Tenant Migration Tool')
        self.migration_button.clicked.connect(self.show_migration_app)
        main_screen_layout.addWidget(self.migration_button)

        self.user_guest_button = QPushButton('User/Guest Creation Tool')
        self.user_guest_button.clicked.connect(self.show_user_guest_creation_app)
        main_screen_layout.addWidget(self.user_guest_button)

        self.main_screen.setLayout(main_screen_layout)
        self.stack.addWidget(self.main_screen)
        self.stack.addWidget(self.migration_app)
        self.stack.addWidget(self.user_guest_creation_app)

        self.back_to_main_button = QPushButton('Back to Main Screen')
        self.back_to_main_button.clicked.connect(self.show_main_screen)
        layout.addWidget(self.back_to_main_button)

        layout.addWidget(self.stack)

        self.show_main_screen()

        self.setLayout(layout)
        self.setWindowTitle('Main Application')
        self.setGeometry(300, 300, 600, 400)
        self.set_default_stylesheet()
        self.show()

    def show_migration_app(self):
        self.stack.setCurrentWidget(self.migration_app)
        self.back_to_main_button.show()
        self.migration_button.hide()
        self.user_guest_button.hide()

    def show_user_guest_creation_app(self):
        self.stack.setCurrentWidget(self.user_guest_creation_app)
        self.back_to_main_button.show()
        self.migration_button.hide()
        self.user_guest_button.hide()

    def show_main_screen(self):
        self.stack.setCurrentWidget(self.main_screen)
        self.back_to_main_button.hide()
        self.migration_button.show()
        self.user_guest_button.show()

    def set_default_stylesheet(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QListWidget, QComboBox, QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

    def set_dark_stylesheet(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b; /* Softer dark gray */
                color: white;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QListWidget, QComboBox, QTextEdit {
                background-color: #3e3e3e; /* Slightly lighter gray */
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)

    def toggle_dark_mode(self):
        if self.dark_mode_enabled:
            self.set_default_stylesheet()
            self.dark_mode_enabled = False
        else:
            self.set_dark_stylesheet()
            self.dark_mode_enabled = True


class MigrationApp(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
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
        self.parent.set_default_stylesheet()

    def toggle_dark_mode(self):
        self.parent.toggle_dark_mode()

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
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None,
                                                self.source_credential, None)
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
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None,
                                                self.source_credential, None)
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
            self.data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, None, None,
                                                self.target_credential, selected_domain)
            for item in items_to_migrate:
                if 'userPrincipalName' in item:
                    created_user = self.data_migration.migrate_user(item)
                    if created_user:
                        self.domain_selector_module.data_display.append(
                            f"Migrated user: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                        if self.migration_actions_module.delete_checkbox.isChecked():
                            self.data_migration.remove_user(item['id'])
                            self.domain_selector_module.data_display.append(
                                f"Removed user from source tenant: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                        self.data_listing_module.item_list.takeItem(
                            self.data_listing_module.item_list.row(selected_items.pop(0)))
                    else:
                        self.domain_selector_module.data_display.append(
                            f"Failed to migrate user: {item.get('displayName', 'N/A')} ({item.get('userPrincipalName', 'N/A')})")
                elif 'mailNickname' in item:
                    created_group = self.data_migration.migrate_group(item)
                    if created_group:
                        self.domain_selector_module.data_display.append(
                            f"Migrated group: {item.get('displayName', 'N/A')} ({item.get('id', 'N/A')})")
                        self.data_listing_module.item_list.takeItem(
                            self.data_listing_module.item_list.row(selected_items.pop(0)))
                    else:
                        self.domain_selector_module.data_display.append(
                            f"Failed to migrate group: {item.get('displayName', 'N/A')} ({item.get('id', 'N/A')})")
        except Exception as e:
            logging.error(f"Failed to migrate items: {e}")
            self.domain_selector_module.data_display.append(f"Failed to migrate items: {e}")


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
