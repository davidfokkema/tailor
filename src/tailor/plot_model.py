import re
from dataclasses import dataclass

import asteval
import lmfit
import numpy as np
import pandas as pd
import xxhash
from numpy.typing import ArrayLike

from tailor.ast_names import rename_variables
from tailor.data_model import DataModel


@dataclass
class Parameter:
    """A fit parameter with boundaries."""

    name: str
    value: float = 1.0
    min: float = float("-inf")
    max: float = float("inf")
    vary: bool = True


class FitError(Exception):
    """Error while performing fit procedure."""


class PlotModel:
    data_model: DataModel
    x_col: str
    y_col: str
    x_err_col: str | None
    y_err_col: str | None
    x_label: str = ""
    y_label: str = ""

    x_min: float | None = None
    x_max: float | None = None
    y_min: float | None = None
    y_max: float | None = None

    _model_expression: str = ""
    _model: lmfit.models.ExpressionModel | None = None
    _parameters: dict[str, Parameter]
    _fit_domain: tuple[float, float] = (float("-inf"), float("inf"))
    _use_fit_domain: bool = False
    _fit_data_checksum: int | None = None

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

        self._parameters = {}
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

    def uses(self, model: DataModel, labels: list[str]) -> bool:
        """Test whether columns are in use by this plot.

        If the listed column labels are in use as an x, y axis or error flags,
        returns True, but only if the columns are from the same data sheet as
        this plot. For example, if you create a plot with columns 'time' and
        'position' from 'Sheet 2', then the columns 'time' and 'position' from
        'Sheet 1' are _not_ used.

        Args:
            model (DataModel): the data model containing the columns under test
            labels (list[str]): the column labels to check

        Returns:
            bool: True if any of the columns are in use.
        """
        if model is not self.data_model:
            return False
        if set(labels) & {self.x_col, self.y_col, self.x_err_col, self.y_err_col}:
            return True
        else:
            return False

    def get_fit_domain(self) -> tuple[float, float]:
        """Get fit domain.

        Returns:
            tuple[float, float]: a tuple of xmin, xmax values.
        """
        return self._fit_domain

    def set_fit_domain(
        self, xmin: float | None = None, xmax: float | None = None
    ) -> None:
        """Set fit domain.

        Sets the fit domain to xmin, xmax. Either of these values may be None.
        In that case that value is not updated. This allows for only setting the
        lower or upper bound of the fit domain.

        Args:
            xmin (float | None, optional): The new lower bound. Defaults to None.
            xmax (float | None, optional): The new upper bound. Defaults to None.
        """
        new_min, new_max = self._fit_domain
        if xmin is not None:
            new_min = xmin
        if xmax is not None:
            new_max = xmax
        if (new_min, new_max) != self._fit_domain:
            self.best_fit = None
            self._fit_domain = (new_min, new_max)

    def get_fit_domain_enabled(self) -> bool:
        """Return if fit domain is used in fitting procedure.

        Returns:
            bool: True if fit domain is used, False otherwise.
        """
        return self._use_fit_domain

    def set_fit_domain_enabled(self, is_enabled: bool) -> None:
        """Set whether fit domain must be used in fitting procedure.

        If this setting is changed, the best fit is invalidated.

        Args:
            is_enabled (bool): True if fit domain must be used, False otherwise.
        """
        if self._use_fit_domain != is_enabled:
            self._use_fit_domain = is_enabled
            self.best_fit = None

    def get_data(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get data values from model.

        If error values are not specified, returns 0.0 for all errors.

        Returns:
            A tuple of NumPy arrays containing x, y, x-error and y-error values.
        """
        df = self._get_data_as_dataframe()
        x, y, x_err, y_err = df.to_numpy().T

        return x, y, x_err, y_err

    def get_data_in_fit_domain(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Get data values from model in fit domain.

        If the fit domain is not specified, return all data. The fit domain
        bounds are inclusive.

        Returns:
            A tuple of NumPy arrays containing x, y, x-error and y-error values.
        """
        if self._use_fit_domain is False:
            return self.get_data()

        df = self._get_data_as_dataframe()
        x0, x1 = self._fit_domain

        x = df["x"]
        df = df[(x0 <= x) & (x <= x1)]

        x, y, x_err, y_err = df.to_numpy().T
        return x, y, x_err, y_err

    def _get_data_as_dataframe(self) -> pd.DataFrame:
        """Get data values from model as dataframe.

        If error values are not specified, returns 0.0 for all errors.

        Returns:
            A Pandas DataFrame containing x, y, x-error and y-error values.
        """
        x = self.data_model.get_column(self.x_col)
        y = self.data_model.get_column(self.y_col)
        if self.x_err_col is not None:
            x_err = self.data_model.get_column(self.x_err_col)
        else:
            x_err = 0.0
        if self.y_err_col is not None:
            y_err = self.data_model.get_column(self.y_err_col)
        else:
            y_err = 0.0

        # Drop NaN and Inf values
        df = pd.DataFrame.from_dict({"x": x, "y": y, "x_err": x_err, "y_err": y_err})
        return df.replace([np.inf, -np.inf], np.nan).dropna()

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

    def update_model_expression(self, expression: str) -> bool:
        """Update the model expression.

        Update the stored (transformed) model expression independent of column
        names. After calling this method, the `parameters` attribute has an
        updated dictionary of model parameters.

        Args:
            expression (str): the model expression.

        Returns:
            True if the expression is successfully updated, False otherwise.
        """
        # remove whitespace after newlines to prevent indentation errors
        expression = re.sub(r"\n\s*", "\n", expression)
        # mapping: name -> label
        mapping = {self.data_model.get_column_name(self.x_col): self.x_col}
        try:
            transformed = rename_variables(expression, mapping)
        except SyntaxError:
            # expression could not be parsed
            self._model_expression = expression
            self._model = None
            self.best_fit = None
            return True
        else:
            if self._model_expression != transformed:
                self._model_expression = transformed
                try:
                    self._model = lmfit.models.ExpressionModel(
                        transformed, independent_vars=[self.x_col]
                    )
                except ValueError:
                    # independent (x) variable not present in expression
                    self._model = None
                else:
                    self.update_model_parameters()
                self.best_fit = None
                return True
        return False

    def is_model_valid(self) -> bool:
        """Return if the model expression is a valid model.

        Returns:
            bool: True if the model is valid, False otherwise.
        """
        if self._model is None:
            return False
        else:
            return True

    def update_model_parameters(self):
        """Update model parameters.

        Comparing the stored model to the stored parameters, determine which
        parameters are newly-defined in the model and must be created and which
        stored parameters are no longer used in the model and must be discarded.
        """
        stored = set(self._parameters.keys())
        current = set(self._model.param_names)

        new = current - stored
        discard = stored - current

        # discard unneeded parameters
        for key in discard:
            self._parameters.pop(key)

        # add new parameters
        for key in new:
            self._parameters[key] = Parameter(name=key)

    def get_parameter_names(self) -> list[str]:
        """Get the names of the model parameters.

        Returns:
            list[str]: a list of parameter names.
        """
        return list(self._parameters.keys())

    def get_parameter_by_name(self, name: str) -> Parameter:
        """Get parameter by name.

        Use the `get_parameter_names()` method to get a list of parameter names.

        Args:
            name (str): the name of the parameter.

        Returns:
            Parameter: the requested parameter object.
        """
        return self._parameters[name]

    def set_parameter_value(self, name: str, value: float) -> None:
        """Set initial value of a parameter.

        Setting a new initial value for the parameter will invalidate the best
        fit.

        Args:
            name (str): name of the parameter
            value (float): new initial value
        """
        self._parameters[name].value = value
        self.best_fit = None

    def set_parameter_min_value(self, name: str, value: float) -> None:
        """Set lower bound of a parameter.

        Setting a new lower bound will invalidate the best fit.

        Args:
            name (str): name of the parameter
            value (float): new lower bound
        """
        self._parameters[name].min = value
        self.best_fit = None

    def set_parameter_max_value(self, name: str, value: float) -> None:
        """Set upper bound of a parameter.

        Setting a new upper bound will invalidate the best fit.

        Args:
            name (str): name of the parameter
            value (float): new upper bound
        """
        self._parameters[name].max = value
        self.best_fit = None

    def set_parameter_vary_state(self, name: str, state: bool) -> None:
        """Set whether to vary a parameter value during fit.

        Setting the vary state to False will fix the parameter value.

        Args:
            name (str): name of the parameter
            state (bool): new vary state
        """
        self._parameters[name].vary = state
        self.best_fit = None

    def get_model_expression(self) -> str:
        """Get model expression.

        Returns:
            str: the model expression.
        """
        mapping = {self.x_col: self.data_model.get_column_name(self.x_col)}
        try:
            return rename_variables(self._model_expression, mapping)
        except SyntaxError:
            # expression could not be parsed
            return self._model_expression

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
        if self._model:
            kwargs = {k: v.value for k, v in self._parameters.items()}
            kwargs[self.x_col] = x
            return self._model.eval(**kwargs)
        else:
            return None

    def perform_fit(self):
        """Fit the model to the data points.

        Fit the model to the data points starting with the initial values for the parameters. If the fit is successful, the `best_fit` object can be used to determine the best-fit values of the parameters.
        """
        if self._model is None:
            return

        params = self._model.make_params(
            **{
                k: {"min": v.min, "value": v.value, "max": v.max, "vary": v.vary}
                for k, v in self._parameters.items()
            }
        )
        data = self.get_data_in_fit_domain()
        self._fit_data_checksum = self.hash_data(data)

        x, y, _, y_err = data
        try:
            self.best_fit = self._model.fit(
                data=y,
                params=params,
                weights=1 / (y_err + 1e-99),
                **{self.x_col: x},
                nan_policy="omit",
            )
        except Exception as exc:
            raise FitError("foo") from exc

    def hash_data(self, data: ArrayLike) -> int:
        """Calculate a hash (checksum) of the data.

        A deterministic hash is calculated for the provided data. This hash can
        then be used as a checksum to determine if some other data is identical
        or different. This determination is slower using checksums than by
        direct comparison, but the checksum has the benefit of being able to
        store just a hash and not a complete copy of the data. Also, by using a
        fast hashing algorithm like xxHash, the slowdown is only a factor 1.5x -
        2x for larger datasets and almost 1x for small datasets.

        Args:
            data (ArrayLike): the data for which to calculate the hash.

        Returns:
            int: the calculated hash (checksum).
        """
        return xxhash.xxh3_64(np.array(data)).intdigest()

    def verify_best_fit_data(self) -> bool:
        """Determine if the given data is identical to the fitted data.

        Sometime after a best fit of the model to the experimental data has been
        determined, that data may change due to the user changing values or
        expressions. This method can determine if the possibly new data is
        identical to the data that was used in the fitting procedure. It returns
        a boolean; True means that the data is identical, False means it is not.
        Furthermore, if the data is not identical, the best fit is invalidated.

        Returns:
            bool: whether the given data is identical or not
        """
        data = self.get_data_in_fit_domain()
        if self.hash_data(data) == self._fit_data_checksum:
            return True
        else:
            self.best_fit = None
            self._fit_data_checksum = None
            return False

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
