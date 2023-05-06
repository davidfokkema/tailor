from PySide6 import QtCore, QtWidgets

app = QtWidgets.QApplication()
checkbox = QtWidgets.QCheckBox()
state = checkbox.checkState()
print(f"{state=}")
# this is True on PySide 6.3 but False on PySide 6.4 !!
print(f"{not state=}")

print(f"{not checkbox.isChecked()=}")
print(f"{checkbox.checkState() == QtCore.Qt.CheckState.Unchecked}")
checkbox.setChecked(True)
print(f"{not checkbox.isChecked()=}")
