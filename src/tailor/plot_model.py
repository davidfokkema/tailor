import re
from dataclasses import dataclass

import asteval
import lmfit
import numpy as np
import pandas as pd

from tailor.ast_names import get_variable_names, rename_variables
from tailor.data_model import DataModel


@dataclass
class Parameter:
    """A fit parameter with boundaries."""

    name: str
    value: float = 1.0
    min: float = float("-inf")
    max: float = float("inf")
    vary: bool = True


class PlotModel:
    data_model: DataModel
    x_col: str
    y_col: str
    x_err_col: str | None
    y_err_col: str | None
    x_label: str
    y_label: str

    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None

    model_expression: str = ""
    model: lmfit.models.ExpressionModel | None = None
    parameters: dict[str, Parameter]
    fit_domain: tuple[float, float] | None = None
    has_fit: bool = False

    def __init__(
        self,
        data_model: DataModel,
        x_col: str,
        y_col: str,
        x_err_col: str | None = None,
        y_err_col: str | None = None,
    ) -> None:
        self.data_model = data_model
        self.x_col = x_col
        self.y_col = y_col
        self.x_err_col = x_err_col
        self.y_err_col = y_err_col
        self.x_label = self.get_x_col_name()
        self.y_label = self.get_y_col_name()

        self.parameters = {}
        self._math_symbols = set(asteval.Interpreter().symtable.keys())

    def get_x_col_name(self) -> str:
        """Get the name of the x variable."""
        return self.data_model.get_column_name(self.x_col)

    def get_y_col_name(self) -> str:
        """Get the name of the y variable."""
        return self.data_model.get_column_name(self.y_col)

    def get_x_err_col_name(self) -> str:
        """Get the name of the x error variable.

        Returns:
            A string with the name of the variable or None if there is no such variable.
        """
        try:
            return self.data_model.get_column_name(self.x_err_col)
        except KeyError:
            return None

    def get_y_err_col_name(self) -> str:
        """Get the name of the y error variable.

        Returns:
            A string with the name of the variable or None if there is no such variable.
        """
        try:
            return self.data_model.get_column_name(self.y_err_col)
        except KeyError:
            return None

    def get_data(self) -> tuple[np.ndarray]:
        """Get data values from model.

        Returns:
            A tuple of NumPy arrays containing x, y, x-error and y-error values.
        """
        x = self.data_model.get_column(self.x_col)
        y = self.data_model.get_column(self.y_col)
        try:
            x_err = self.data_model.get_column(self.x_err_col)
        except KeyError:
            x_err = 0.0

        try:
            y_err = self.data_model.get_column(self.y_err_col)
        except KeyError:
            y_err = 0.0

        # Drop NaN and Inf values
        df = pd.DataFrame.from_dict({"x": x, "y": y, "x_err": x_err, "y_err": y_err})
        df.dropna(inplace=True)
        x, y, x_err, y_err = df.to_numpy().T

        return x, y, x_err, y_err

    def get_limits_from_data(self, padding=0.05) -> tuple[float]:
        """Get plot limits from the data points.

        Return the minimum and maximum values of the data points, taking the
        error bars into account.

        Args:
            padding: the relative amount of padding to add to the axis limits.
                Default is .05.

        Returns:
            Tuple of four float values (xmin, xmax, ymin, ymax).
        """
        x, y, x_err, y_err = self.get_data()

        xmin = min(x - x_err)
        xmax = max(x + x_err)
        ymin = min(y - y_err)
        ymax = max(y + y_err)

        xrange = xmax - xmin
        yrange = ymax - ymin

        xmin -= padding * xrange
        xmax += padding * xrange
        ymin -= padding * yrange
        ymax += padding * yrange

        return xmin, xmax, ymin, ymax

    def update_model_expression(self, expression: str) -> None:
        """Update the model expression.

        Update the stored (transformed) model expression independent of column
        names. After calling this method, the `parameters` attribute has an
        updated dictionary of model parameters.

        Args:
            expression (str): the model expression.
        """
        # remove whitespace after newlines to prevent indentation errors
        expression = re.sub(r"\n\s*", "\n", expression)
        # mapping: names -> labels, so must reverse _col_names mapping
        mapping = {v: k for k, v in self.data_model._col_names.items()}
        try:
            transformed = rename_variables(expression, mapping)
        except SyntaxError:
            # expression could not be parsed
            self.model_expression = expression
            self.model = None
        else:
            self.model_expression = transformed
            try:
                self.model = lmfit.models.ExpressionModel(
                    transformed, independent_vars=[self.x_col]
                )
            except ValueError:
                # independent (x) variable not present in expression
                self.model = None
            else:
                self.update_model_parameters()

    def update_model_parameters(self):
        stored = set(self.parameters.keys())
        current = set(self.model.param_names)

        new = current - stored
        discard = stored - current

        # discard unneeded parameters
        for key in discard:
            self.parameters.pop(key)

        # add new parameters
        for key in new:
            self.parameters[key] = Parameter(name=key)

    def get_model_expression(self) -> str:
        """Get model expression.

        Returns:
            str: the model expression.
        """
        mapping = dict(self.data_model._col_names.items())
        try:
            return rename_variables(self.model_expression, mapping)
        except SyntaxError:
            # expression could not be parsed
            return self.model_expression

    def evaluate_model(self, x: np.ndarray) -> np.ndarray | None:
        """Evaluate the fit model.

        Evaluate the fit model using the current values for the initial
        parameters at the supplied x-values. If no model is currently defined,
        return None.

        Args:
            x (np.ndarray): the x-values for which to evaluate the model.

        Returns:
            np.ndarray | None: the evaluated y-values or None
        """
        if self.model:
            kwargs = {k: v.value for k, v in self.parameters.items()}
            kwargs[self.x_col] = x
            return self.model.eval(**kwargs)
        else:
            return None

    # def get_params_and_update_model(self):
    #     """Get parameter names and update the model function.

    #     Based on the mathematical expression for the model function, determine
    #     what are the parameters of the model. If the model compiles, the model
    #     object is updated as well.

    #     Raises VariableError when the dependent variable is part of the model
    #     function.

    #     Returns:
    #         A set of parameter names.
    #     """
    #     model_expr = self.ui.model_func.toPlainText().replace("\n", "")
    #     code = compile(model_expr, "<string>", "eval")
    #     params = set(code.co_names) - set([self.x_var]) - self._symbols
    #     if self.y_var in params:
    #         raise VariableError(
    #             f"Dependent variable {self.y_var} must not be in function definition"
    #         )
    #     else:
    #         try:
    #             self.model = models.ExpressionModel(
    #                 model_expr, independent_vars=[self.x_var]
    #             )
    #         except ValueError as exc:
    #             raise VariableError(exc)
    #         return params

    # def perform_fit(self):
    #     """Perform fit and plot best fit model.

    #     Fits the model function to the data to estimate best fit parameters.
    #     When the fit is successful, the results are given in the result box and
    #     the best fit is plotted on top of the data.
    #     """
    #     if self.model is None:
    #         self.main_window.ui.statusbar.showMessage(
    #             "FIT FAILED: please fix your model first."
    #         )
    #         return

    #     # set model parameter hints
    #     param_hints = self.get_parameter_hints()
    #     for p, hints in param_hints.items():
    #         self.model.set_param_hint(p, **hints)

    #     # select data for fit
    #     if self.ui.use_fit_domain.isChecked():
    #         xmin = self.ui.fit_start_box.value()
    #         xmax = self.ui.fit_end_box.value()
    #         if xmin > xmax:
    #             self.main_window.ui.statusbar.showMessage(
    #                 "ERROR: domain start is larger than end.", timeout=MSG_TIMEOUT
    #             )
    #             return
    #         condition = (xmin <= self.x) & (self.x <= xmax)
    #         x = self.x[condition]
    #         y = self.y[condition]
    #         if self.y_err_var is not None:
    #             y_err = self.y_err[condition]
    #         else:
    #             y_err = None
    #     else:
    #         x = self.x
    #         y = self.y
    #         if self.y_err_var is not None:
    #             y_err = self.y_err
    #         else:
    #             y_err = None

    #     # perform fit
    #     kwargs = {self.x_var: x}
    #     if y_err is not None:
    #         kwargs["weights"] = 1 / y_err
    #     try:
    #         self.fit = self.model.fit(y, **kwargs)
    #     except Exception as exc:
    #         self.main_window.ui.statusbar.showMessage(f"FIT FAILED: {exc}")
    #     else:
    #         self.update_info_box()
    #         self.update_best_fit_plot()
    #         self.ui.show_initial_fit.setChecked(False)
    #         self.main_window.ui.statusbar.showMessage(
    #             "Updated fit.", timeout=MSG_TIMEOUT
    #         )
