import traceback

from PySide6 import QtWidgets


def show_warning_dialog(parent, msg):
    """Show a warning dialog.

    Args:
        parent (QtWidgets.QWidget): the parent widget
        msg (str): the message
    """
    dialog = QtWidgets.QMessageBox(parent=parent)
    dialog.setIcon(QtWidgets.QMessageBox.Warning)
    dialog.setText(msg)
    dialog.exec()


def show_error_dialog(parent, msg):
    """Show an error dialog.

    Args:
        parent (QtWidgets.QWidget): the parent widget
        msg (str): the message
    """
    dialog = QtWidgets.QMessageBox(parent=parent)
    dialog.setIcon(QtWidgets.QMessageBox.Critical)
    dialog.setText(msg)
    dialog.exec()


def show_exception(parent, exc, title, text):
    """Show a messagebox with detailed exception information.

    Args:
        exc: the exception.
        title: short header text.
        text: longer informative text describing the problem.
    """
    msg = QtWidgets.QMessageBox(parent=parent)
    msg.setText(title)
    msg.setInformativeText(text)
    msg.setDetailedText("".join(traceback.format_exception(exc)))
    msg.setStyleSheet("QLabel{min-width: 400px;}")
    msg.exec()
