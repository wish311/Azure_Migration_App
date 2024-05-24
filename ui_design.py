import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QListWidget, QApplication
from azure.identity import InteractiveBrowserCredential
import jwt
from data_migration import DataMigration

class MigrationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.source_credential = None
        self.target_credential = None
        self.source_tenant_id = None
        self.target_tenant_id = None
        self.client_id = 'YOUR_CLIENT_ID'
        self.client_secret = 'YOUR_CLIENT_SECRET'
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.auth_button_source = QPushButton('Sign in to Source Tenant')
        self.auth_button_source.clicked.connect(self.authenticate_source_tenant)
        layout.addWidget(self.auth_button_source)

        self.auth_button_destination = QPushButton('Sign in to Destination Tenant')
        self.auth_button_destination.clicked.connect(self.authenticate_destination_tenant)
        layout.addWidget(self.auth_button_destination)

        self.data_list = QListWidget()
        self.data_list.addItems(['Users', 'Groups', 'Files'])
        layout.addWidget(self.data_list)

        self.migrate_button = QPushButton('Migrate Data')
        self.migrate_button.clicked.connect(self.migrate_data)
        layout.addWidget(self.migrate_button)

        self.setLayout(layout)
        self.setWindowTitle('Azure Tenant Migration')
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
        """)
        self.show()

    def authenticate_source_tenant(self):
        self.source_credential = InteractiveBrowserCredential()
        token = self.source_credential.get_token("https://management.azure.com/.default")
        self.source_tenant_id = self.extract_tenant_id(token.token)
        print("Authenticated Source Tenant")

    def authenticate_destination_tenant(self):
        self.target_credential = InteractiveBrowserCredential()
        token = self.target_credential.get_token("https://management.azure.com/.default")
        self.target_tenant_id = self.extract_tenant_id(token.token)
        print("Authenticated Destination Tenant")

    def extract_tenant_id(self, token):
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded['tid']

    def migrate_data(self):
        data_selection = [item.text() for item in self.data_list.selectedItems()]
        if self.source_credential and self.target_credential and self.source_tenant_id and self.target_tenant_id:
            data_migration = DataMigration(self.source_tenant_id, self.target_tenant_id, self.client_id, self.client_secret)
            data_migration.migrate_data(data_selection)
        else:
            print("Please authenticate both tenants before migrating data.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MigrationApp()
    sys.exit(app.exec_())
