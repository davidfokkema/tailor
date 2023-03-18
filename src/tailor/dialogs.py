from PySide6 import QtWidgets


def show_warning_dialog(parent, msg):
    """Show a warning dialog.

    Args:
        parent (QtWidgets.QWidget): the parent widget
        msg (str): the message
    """
    dialog = QtWidgets.QMessageBox(parent=parent)
    dialog.setIcon(dialog.Warning)
    dialog.setText(msg)
    dialog.exec()
