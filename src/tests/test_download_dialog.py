import webbrowser

from PySide6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        vbox = QtWidgets.QVBoxLayout(central_widget)

        button = QtWidgets.QPushButton("Check")
        vbox.addWidget(button)
        button.clicked.connect(self.check_updates)

        self.show()

    def check_updates(self):
        dialog = QtWidgets.QMessageBox(parent=self)
        dialog.setText("Hi there!")
        dialog.setInformativeText("This is fun.")
        dialog.setStandardButtons(dialog.Ok | dialog.Cancel)

        dialog.button(dialog.Ok).setText("Download Update")
        dialog.button(dialog.Cancel).setText("Skip Update")

        value = dialog.exec()
        match value:
            case dialog.Ok:
                print("Yes, download!")
                # if app is in the main event loop, ask to quit so user can
                # install update
                QtWidgets.QApplication.instance().quit()
                # after possible 'save your project' dialogs, download update
                webbrowser.open(
                    "https://github.com/davidfokkema/tailor/releases/latest"
                )
                # if not, return with True to signal that the user wants the update
                return True
            case dialog.Cancel:
                print("Next!")
                return False
            case default:
                print("Oh my")
                return None


if __name__ == "__main__":
    qapp = QtWidgets.QApplication()
    main = MainWindow()

    if not main.check_updates():
        # user does not want to install update
        # so run the app
        qapp.exec()
