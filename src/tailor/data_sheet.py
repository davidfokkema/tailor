from PySide6 import QtWidgets

from tailor.ui_data_sheet import Ui_DataSheet


class DataSheet(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_DataSheet()
        self.ui.setupUi(self)
