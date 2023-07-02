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
    best_fit: lmfit.model.ModelResult | None = None

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

    def get_data(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
        """Update model parameters.

        Comparing the stored model to the stored parameters, determine which
        parameters are newly-defined in the model and must be created and which
        stored parameters are no longer used in the model and must be discarded.
        """
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

    def perform_fit(self):
        """Fit the model to the data points.

        Fit the model to the data points starting with the initial values for the parameters. If the fit is successful, the `best_fit` object can be used to determine the best-fit values of the parameters.
        """
        if self.model is None:
            return

        params = self.model.make_params(
            **{
                k: {"min": v.min, "value": v.value, "max": v.max, "vary": v.vary}
                for k, v in self.parameters.items()
            }
        )
        x, y, _, y_err = self.get_data()
        self.best_fit = self.model.fit(
            data=y,
            params=params,
            weights=1 / (y_err + 1e-99),
            **{self.x_col: x},
            nan_policy="omit"
        )

    def evaluate_best_fit(self, x: np.ndarray) -> np.ndarray | None:
        """Evaluate the fit model with best-fit parameters.

        Evaluate the fit model using the values for the best-fit parameters at
        the supplied x-values. If no model is currently defined, return None.

        Args:
            x (np.ndarray): the x-values for which to evaluate the model.

        Returns:
            np.ndarray | None: the evaluated y-values or None
        """
        if self.best_fit:
            return self.best_fit.eval(**{self.x_col: x})
        else:
            return None
