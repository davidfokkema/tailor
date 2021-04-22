import pkg_resources
from PyQt5 import uic, QtWidgets
import pandas as pd


DELIMITER_CHOICES = {"detect": None, "comma": ",", "tab": "\t", "space": " "}
NUM_FORMAT_CHOICES = {"1,000.0": (".", ","), "1.000,0": (",", ".")}


class CSVFormatDialog(QtWidgets.QDialog):
    def __init__(self, filename):
        """Create the CSV file format selection dialog."""
        super().__init__()

        self.filename = filename

        uic.loadUi(
            pkg_resources.resource_stream("tailor.resources", "csv_format_dialog.ui"),
            self,
        )
        self.delimiter_box.addItems(DELIMITER_CHOICES.keys())
        self.num_format_box.addItems(NUM_FORMAT_CHOICES.keys())

        self.delimiter_box.currentIndexChanged.connect(self.show_preview)
        self.num_format_box.currentIndexChanged.connect(self.show_preview)
        self.use_header_box.stateChanged.connect(self.show_preview)
        self.header_row_box.valueChanged.connect(self.show_preview)

        self.show_preview()

    def show_preview(self):
        """Show a preview of the CSV data."""
        (
            delimiter,
            decimal,
            thousands,
            header,
        ) = self.get_format_parameters()
        df = pd.read_csv(
            self.filename,
            delimiter=delimiter,
            decimal=decimal,
            thousands=thousands,
            header=header,
        )
        self.preview_box.setPlainText(df.to_string())

    def get_format_parameters(self):
        """Get CSV format parameters

        Returns:
            delimiter, decimal, thousands, header: a tuple of format options.
        """
        delimiter = DELIMITER_CHOICES[self.delimiter_box.currentText()]
        decimal, thousands = NUM_FORMAT_CHOICES[self.num_format_box.currentText()]
        if self.use_header_box.isChecked():
            header = self.header_row_box.value()
        else:
            header = None
        return delimiter, decimal, thousands, header