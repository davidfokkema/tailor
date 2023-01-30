from PySide6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(500, 300)
        self.scrollable = QtWidgets.QScrollArea()
        self.scrollable.setWidgetResizable(True)

        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        widget.setLayout(layout)

        self.setCentralWidget(self.scrollable)
        self.scrollable.setWidget(widget)

        for _ in range(10):
            layout.addWidget(QtWidgets.QPushButton("OK"))

        for _ in range(10):
            layout.addWidget(QtWidgets.QPushButton("OK"))


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    app = MainWindow()

    app.show()
    qapp.exec()
