import sys

sys.path.append("src/")

from unittest.mock import Mock

import tailor.data_model


def test_recalculate_column():
    data_model = tailor.data_model.DataModel(Mock(name="main_app"))

    data_model.insert_calculated_column(2)

    # an integer
    assert data_model.recalculate_column("new1", "1") == True
    assert data_model._is_calculated_column_valid["new1"] == True

    # a float
    assert data_model.recalculate_column("new1", "1.0") == True
    assert data_model._is_calculated_column_valid["new1"] == True

    # a pandas.Series
    assert data_model.recalculate_column("new1", "x") == True
    assert data_model._is_calculated_column_valid["new1"] == True

    # a string
    assert data_model.recalculate_column("new1", "'a'") == False
    assert data_model._is_calculated_column_valid["new1"] == False

    # an empty expression
    assert data_model.recalculate_column("new1", "") == False
    assert data_model._is_calculated_column_valid["new1"] == False

    # an evaluation error
    assert data_model.recalculate_column("new1", "1 /") == False
    assert data_model._is_calculated_column_valid["new1"] == False

    # an unknown symbol
    assert data_model.recalculate_column("new1", "1 * foo") == False
    assert data_model._is_calculated_column_valid["new1"] == False


if __name__ == "__main__":
    test_recalculate_column()
