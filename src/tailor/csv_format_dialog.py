from pathlib import Path

import pkg_resources
from PyQt5 import uic, QtWidgets
import pandas as pd


DELIMITER_CHOICES = {
    "detect": None,
    "comma": ",",
    "semicolon": ";",
    "tab": "\t",
    "space": " ",
}
NUM_FORMAT_CHOICES = {"1,000.0": (".", ","), "1.000,0": (",", ".")}


class CSVFormatDialog(QtWidgets.QDialog):
    def __init__(self, filename):
        """Create the CSV file format selection dialog."""
        super().__init__()

        self.filename = Path(filename).expanduser()

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
        self.preview_choice.buttonClicked.connect(self.show_preview)

        self.show_preview()

    def show_preview(self):
        """Show a preview of the CSV data."""
        if self.preview_choice.checkedButton() == self.preview_csv_button:
            (
                delimiter,
                decimal,
                thousands,
                header,
                skiprows,
            ) = self.get_format_parameters()
            try:
                df = pd.read_csv(
                    self.filename,
                    delimiter=delimiter,
                    decimal=decimal,
                    thousands=thousands,
                    header=header,
                    skiprows=skiprows,
                )
            except pd.errors.ParserError as exc:
                text = f"Parse Error: {exc!s}"
            else:
                text = df.to_string()
        else:
            with open(self.filename) as f:
                text = "".join(f.readlines())
        self.preview_box.setPlainText(text)

    def get_format_parameters(self):
        """Get CSV format parameters

        Returns:
            delimiter, decimal, thousands, header: a tuple of format options.
        """
        delimiter = DELIMITER_CHOICES[self.delimiter_box.currentText()]
        decimal, thousands = NUM_FORMAT_CHOICES[self.num_format_box.currentText()]
        if self.use_header_box.isChecked():
            header = self.header_row_box.value()
            skiprows = 0
        else:
            header = None
            skiprows = self.header_row_box.value()
        return delimiter, decimal, thousands, header, skiprows