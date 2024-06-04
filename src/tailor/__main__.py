import importlib
import sys
import threading

from PySide6 import QtWidgets

PREFLIGHT_MODULES = [
    "pydantic",
    "numpy",
    "scipy.optimize",
    "scipy.stats",
    "matplotlib.pyplot",
    "pandas",
    "lmfit",
    "libcst",
    "PySide6",
    "pyqtgraph",
]


class UserInterface(QtWidgets.QMainWindow):
    def __init__(self):
        # roep de __init__() aan van de parent class
        super().__init__()

        # elk QMainWindow moet een central widget hebben
        # hierbinnen maak je een layout en hang je andere widgets
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        # voeg geneste layouts en widgets toe
        vbox = QtWidgets.QVBoxLayout(central_widget)
        self.label = QtWidgets.QLabel("Importing...")
        vbox.addWidget(self.label)

        self.preflight_thread = threading.Thread(target=self.preflight)
        self.preflight_thread.start()

    def preflight(self):
        for module in PREFLIGHT_MODULES:
            self.label.setText(f"Importing module {module}")
            importlib.import_module(module)
        app.exit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    app.exec()
    app.shutdown()

    print("done")

    from tailor.app import main

    main()
