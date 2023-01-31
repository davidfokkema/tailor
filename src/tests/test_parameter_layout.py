from PySide6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.vbox = QtWidgets.QVBoxLayout()
        self.central_widget.setLayout(self.vbox)


def test_parameter_layout(main):
    for idx in range(3):
        widget = QtWidgets.QWidget(objectName=f"par_{idx}")
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)
        layout.addWidget(QtWidgets.QLabel("1"))
        layout.addWidget(QtWidgets.QSpinBox(objectName="value"))
        layout.addWidget(QtWidgets.QLabel("3"))
        main.vbox.addWidget(widget)

    print(f"{main.central_widget.children()=}")
    print(
        f"{main.central_widget.findChild(QtWidgets.QWidget, 'par_2').findChild(QtWidgets.QWidget, 'value')=}"
    )


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    main = MainWindow()
    test_parameter_layout(main)
    main.show()
    qapp.exec()
