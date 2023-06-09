from unittest.mock import Mock, sentinel

import pytest
from pytest_mock import MockerFixture

from tailor.data_model import DataModel
from tailor.plot_model import PlotModel


@pytest.fixture()
def model(mocker: MockerFixture):
    return PlotModel(
        Mock(spec=DataModel),
        sentinel.x_col,
        sentinel.y_col,
        sentinel.x_err_col,
        sentinel.y_err_col,
    )


class TestImplementationDetails:
    def test_init_sets_attributes(self, model: PlotModel):
        assert model.x_col == sentinel.x_col
        assert model.y_col == sentinel.y_col
        assert model.x_err_col == sentinel.x_err_col
        assert model.y_err_col == sentinel.y_err_col
        assert isinstance(model.data_model, DataModel) is True
