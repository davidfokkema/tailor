from PySide6 import QtWidgets

from tailor.data_sheet import DataSheet
from tailor.plot_tab import PlotTab
from tailor.ui_data_source_dialog import Ui_DataSourceDialog


class DataSourceDialog(QtWidgets.QDialog):
    def __init__(self, plot: PlotTab, data_sheets: list[DataSheet]) -> None:
        super().__init__()
        self.ui = Ui_DataSourceDialog()
        self.ui.setupUi(self)

        self.plot = plot
        self.data_sheets = data_sheets
        self.ui.data_source_box.addItems([s.name for s in data_sheets])
        self.ui.data_source_box.setCurrentIndex(data_sheets.index(plot.data_sheet))
        self.update_vars()

        self.ui.data_source_box.currentIndexChanged.connect(self.update_vars)

    def update_vars(self) -> None:
        data_sheet = self.data_sheets[self.ui.data_source_box.currentIndex()]
        choices = [None] + data_sheet.model.columnNames()
        for var in ["x", "y", "x_err", "y_err"]:
            box: QtWidgets.QComboBox = getattr(self.ui, f"{var}_box")
            box.clear()
            box.addItems(choices)
            # try to set the var box to the column that is currently
            # used in the plot
            try:
                label = getattr(self.plot.model, f"{var}_col")
                col_name = self.plot.model.data_model.get_column_name(label)
            except KeyError:
                # the column does not exist in the currently selected
                # data sheet
                pass
            else:
                box.setCurrentText(col_name)
