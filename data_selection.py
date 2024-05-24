from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QTextEdit, QListWidgetItem, QComboBox, QPushButton, QCheckBox
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
