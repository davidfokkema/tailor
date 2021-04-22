import pkg_resources
from PyQt5 import uic, QtWidgets


DELIMITER_CHOICES = {"detect": None, "comma": ",", "tab": "\t", "space": " "}
NUM_FORMAT_CHOICES = {"1,000.0": (".", ","), "1.000,0": (",", ".")}


class CSVFormatDialog(QtWidgets.QDialog):
    def __init__(self):
        """Create the CSV file format selection dialog."""
        super().__init__()
        uic.loadUi(
            pkg_resources.resource_stream("tailor.resources", "csv_format_dialog.ui"),
            self,
        )
        self.delimiter_box.addItems(DELIMITER_CHOICES.keys())
        self.num_format_box.addItems(NUM_FORMAT_CHOICES.keys())