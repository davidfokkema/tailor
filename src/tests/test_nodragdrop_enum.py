from PySide6 import QtWidgets


class A(QtWidgets.QTableView):
    pass


app = QtWidgets.QApplication()

QtWidgets.QTableView.NoDragDrop
a = QtWidgets.QTableView()
# this crashes. The class has an attribute, but the instance does _not_?
a.NoDragDrop
