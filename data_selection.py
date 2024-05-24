class DataSelection:
    def __init__(self):
        self.selected_data_types = []

    def select_data_types(self, data_list_widget):
        self.selected_data_types = [item.text() for item in data_list_widget.selectedItems()]

    def get_selected_data_types(self):
        return self.selected_data_types
