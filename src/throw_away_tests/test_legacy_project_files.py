import sys

sys.path.append("src/")

from pathlib import Path

from PySide6 import QtWidgets

from tailor.app import Application

if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = Application()

    app = Application(add_sheet=False)
    app.load_project(Path.home() / "Desktop" / "legacy-test.tlr")

    app.show()
    qapp.exec()
    qapp.quit()
