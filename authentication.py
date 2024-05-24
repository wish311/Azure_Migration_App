from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

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
