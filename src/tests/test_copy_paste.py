import sys

sys.path.append("src/")


import IPython
import numpy as np
import pandas as pd
from PySide6 import QtCore, QtWidgets

from tailor.app import Application

SELECT = QtCore.QItemSelectionModel.SelectionFlag.Select
TOGGLE = QtCore.QItemSelectionModel.SelectionFlag.Toggle


def test_copy_paste():
    qapp = QtWidgets.QApplication()
    app = Application()

    x = np.arange(20)
    app.data_model.beginResetModel()
    app.data_model._data = pd.DataFrame.from_dict(
        {"x": x, "y": x**2, "z": x / 2, "a": x * 2, "b": np.sin(x)}
    )
    app.data_model.endResetModel()

    app.ui.show()

    set_selection(app, 1, 1, 3, 8, SELECT)
    set_selection(app, 2, 2, 2, 4, TOGGLE)
    set_selection(app, 4, 9, 4, 9, SELECT)
    app.copy_selected_cells()

    text = """\
1.0	0.5	2.0	
4.0		4.0	
9.0		6.0	
16.0		8.0	
25.0	2.5	10.0	
36.0	3.0	12.0	
49.0	3.5	14.0	
64.0	4.0	16.0	
			0.4121184852"""
    assert app.clipboard.text() == text

    app.ui.data_view.setCurrentIndex(app.data_model.createIndex(3, 0))
    app.paste_cells()

    data = """\
       x      y     z          a         b
0    0.0    0.0   0.0   0.000000  0.000000
1    1.0    1.0   0.5   2.000000  0.841471
2    2.0    4.0   1.0   4.000000  0.909297
3    1.0    0.5   2.0        NaN  0.141120
4    4.0    NaN   4.0        NaN -0.756802
5    9.0    NaN   6.0        NaN -0.958924
6   16.0    NaN   8.0        NaN -0.279415
7   25.0    2.5  10.0        NaN  0.656987
8   36.0    3.0  12.0        NaN  0.989358
9   49.0    3.5  14.0        NaN  0.412118
10  64.0    4.0  16.0        NaN -0.544021
11   NaN    NaN   NaN   0.412118 -0.999990
12  12.0  144.0   6.0  24.000000 -0.536573
13  13.0  169.0   6.5  26.000000  0.420167
14  14.0  196.0   7.0  28.000000  0.990607
15  15.0  225.0   7.5  30.000000  0.650288
16  16.0  256.0   8.0  32.000000 -0.287903
17  17.0  289.0   8.5  34.000000 -0.961397
18  18.0  324.0   9.0  36.000000 -0.750987
19  19.0  361.0   9.5  38.000000  0.149877"""
    assert str(app.data_model._data) == data

    # IPython.embed()

    qapp.exec()


def set_selection(app, x1, y1, x2, y2, flag):
    app.selection.select(
        QtCore.QItemSelection(
            app.data_model.createIndex(y1, x1),
            app.data_model.createIndex(y2, x2),
        ),
        flag,
    )


if __name__ == "__main__":
    test_copy_paste()
