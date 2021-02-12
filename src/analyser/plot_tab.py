from PyQt5 import uic, QtWidgets
import pyqtgraph as pg
import pkg_resources
import numpy as np
from lmfit import models
import asteval


class VariableError(RuntimeError):
    pass


class PlotTab(QtWidgets.QWidget):

    x = None
    y = None
    x_err = None
    y_err = None

    def __init__(self, data_model):
        super().__init__()

        self.data_model = data_model
        uic.loadUi(pkg_resources.resource_stream("analyser", "plot_tab.ui"), self)

        self.param_layout = QtWidgets.QFormLayout()
        self.parameter_box.setLayout(self.param_layout)
        self._params = {}
        self._symbols = set(asteval.Interpreter().symtable.keys())

        self._initial_param_plot = self.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="b", width=2)
        )
        self._fit_plot = self.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="r", width=2)
        )

        self.model_func.textEdited.connect(self.update_fit_params)
        self.fit_button.clicked.connect(self.perform_fit)

    def create_plot(self, x_var, y_var, x_err, y_err):
        x, y = self.data_model.get_columns([x_var, y_var])
        self.x, self.y = x, y
        if x_err:
            self.x_err = self.data_model.get_column(x_err)
            width = 2 * self.x_err
        else:
            width = None
        if y_err:
            self.y_err = self.data_model.get_column(y_err)
            height = 2 * self.y_err
        else:
            height = None
        self.plot_widget.plot(
            x, y, symbol="o", pen=None, symbolSize=5, symbolPen="k", symbolBrush="k",
        )
        error_bars = pg.ErrorBarItem(x=x, y=y, width=width, height=height)
        self.plot_widget.addItem(error_bars)
        self.plot_widget.setLabel("left", y_var)
        self.plot_widget.setLabel("bottom", x_var)
        self.update_function_label(y_var)
        self._y_var = y_var
        self._x_var = x_var

    def update_function_label(self, variable):
        label_text = self.model_func_label.text()
        title, _, _ = label_text.partition(":")
        new_label_text = f"{title}:  {variable} ="
        self.model_func_label.setText(new_label_text)

    def update_fit_params(self):
        try:
            params = self.get_params_from_model()
        except (SyntaxError, VariableError) as exc:
            print(exc)
            return
        else:
            old_params = set(self._params)
            self.add_params_to_layout(params - old_params)
            self.remove_params_from_layout(old_params - params)
            self.plot_initial_model()

    def get_params_from_model(self):
        model_expr = self.model_func.text()
        code = compile(model_expr, "<string>", "eval")
        params = set(code.co_names) - set(self._x_var) - self._symbols
        if self._y_var in params:
            raise VariableError(
                f"Dependent variable {self._y_var} must not be in function definition"
            )
        else:
            self.model = models.ExpressionModel(
                model_expr, independent_vars=[self._x_var]
            )
            return params

    def add_params_to_layout(self, params):
        for p in params:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setValue(1.0)
            spinbox.valueChanged.connect(self.plot_initial_model)
            self._params[p] = spinbox
            self.param_layout.addRow(p, spinbox)

    def remove_params_from_layout(self, params):
        for p in params:
            self.param_layout.removeRow(self._params[p])
            del self._params[p]

    def plot_initial_model(self):
        # FIXME Problem for constants like y = a
        x = np.linspace(0, 10, 100)
        kwargs = {k: v.value() for k, v in self._params.items()}
        kwargs[self._x_var] = x
        y = self.model.eval(**kwargs)

        self._initial_param_plot.setData(x, y)

    def perform_fit(self):
        kwargs = {k: v.value() for k, v in self._params.items()}
        params = self.model.make_params(**kwargs)

        kwargs = {self._x_var: self.x}
        if self.y_err is not None:
            kwargs["weights"] = 1 / self.y_err
        fit = self.model.fit(self.y, params=params, **kwargs)
        self.result_box.setPlainText(fit.fit_report())

        x = np.linspace(0, 10, 100)
        y = fit.eval(**{self._x_var: x})
        self._fit_plot.setData(x, y)
