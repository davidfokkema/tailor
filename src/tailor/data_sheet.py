from PySide6 import QtWidgets

from tailor.ui_data_sheet import Ui_DataSheet


class DataSheet(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_DataSheet()
        self.ui.setupUi(self)

        # connect button signals
        self.ui.add_column_button.clicked.connect(self.add_column)
        self.ui.add_calculated_column_button.clicked.connect(self.add_calculated_column)

        # user interface events
        self.ui.data_view.horizontalHeader().sectionMoved.connect(self.column_moved)
        self.ui.name_edit.textEdited.connect(self.rename_column)
        self.ui.formula_edit.textEdited.connect(self.update_column_expression)
        self.ui.create_plot_button.clicked.connect(self.ask_and_create_plot_tab)

        # Start at (0, 0)
        self.ui.data_view.setCurrentIndex(self.data_model.createIndex(0, 0))
