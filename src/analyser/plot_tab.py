"""Tab widget containing plot with associated user interface.

A widget containing a scatter plot of some data columns with user interface
elements to specify a mathematical model to fit to the model.
"""

from PyQt5 import uic, QtWidgets
import pyqtgraph as pg
import pkg_resources
import numpy as np
from lmfit import models
import asteval


class VariableError(RuntimeError):
    pass


class PlotTab(QtWidgets.QWidget):
    """Tab widget containing plot with associated user interface.

    A widget containing a scatter plot of some data columns with user interface
    elements to specify a mathematical model to fit to the model.
    """

    x = None
    y = None
    x_err = None
    y_err = None

    def __init__(self, data_model):
        """Initialize the widget.

        Args:
            data_model: the data model holding the data.
        """
        super().__init__()

        self.data_model = data_model
        uic.loadUi(
            pkg_resources.resource_stream("analyser.resources", "plot_tab.ui"), self
        )

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
        """Create a plot in the widget.

        Create a plot from data in the columns specified by the given column
        names.

        Args:
            x_var: a string containing the name of the column with x values.
            y_var: a string containing the name of the column with y values.
            x_err: a string containing the name of the column with x error
                values.
            y_err: a string containing the name of the column with y error
                values.
        """
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
        """Update function label.

        Updates the text label next to the model function input field. The label
        will contain the name of the dependent variable. For example, "y = ".

        Args:
            variable: a string containing the name of the dependent variable.
        """
        label_text = self.model_func_label.text()
        title, _, _ = label_text.partition(":")
        new_label_text = f"{title}:  {variable} ="
        self.model_func_label.setText(new_label_text)

    def update_fit_params(self):
        """Update fit parameters.

        Gets parameter names from the model function and updates the layout to
        add new parameters and remove parameters which are no longer part of the
        model.
        """
        try:
            params = self.get_params_from_model()
        except (SyntaxError, VariableError) as exc:
            print(exc)
            return
        else:
            old_params = set(self._params)
            self.add_params_to_ui(params - old_params)
            self.remove_params_from_ui(old_params - params)
            self.plot_initial_model()

    def get_params_from_model(self):
        """Get parameter names from the model function.

        Based on the mathematical expression for the model function, determine what are the parameters of the model.

        Raises VariableError when the dependent variable is part of the model function.

        Returns:
            A set of parameter names.
        """
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

    def add_params_to_ui(self, params):
        """Add parameters to user interface.

        When the model function is changed and certain parameters are now part
        of the expression, they need to be added to the user interface.
        
        Args:
            params: a list of parameter names to add to the user interface.
        """
        for p in params:
            spinbox = QtWidgets.QDoubleSpinBox(
                value=1.0,
                decimals=6,
                minimum=-1e6,
                maximum=1e6,
                stepType=QtWidgets.QDoubleSpinBox.AdaptiveDecimalStepType,
            )
            spinbox.valueChanged.connect(self.plot_initial_model)
            self._params[p] = spinbox
            self.param_layout.addRow(p, spinbox)

    def remove_params_from_ui(self, params):
        """Remove parameters from user interface.

        When the model function is changed and certain parameters are no longer
        part of the expression, remove them from the user interface.

        Args:
            params: a list of parameter names to remove from the user interface.
        """
        for p in params:
            self.param_layout.removeRow(self._params[p])
            del self._params[p]

    def plot_initial_model(self):
        """Plot model with initial parameters.

        Plots the model with the initial parameters as given in the user
        interface.
        """
        # FIXME Problem for constants like y = a
        x = np.linspace(0, 10, 100)
        kwargs = {k: v.value() for k, v in self._params.items()}
        kwargs[self._x_var] = x
        y = self.model.eval(**kwargs)

        self._initial_param_plot.setData(x, y)

    def perform_fit(self):
        """Perform fit and plot best fit model.

        Fits the model function to the data to estimate best fit parameters.
        When the fit is successful, the results are given in the result box and
        the best fit is plotted on top of the data.
        """
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
