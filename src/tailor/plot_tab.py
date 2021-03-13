"""Tab widget containing plot with associated user interface.

A widget containing a scatter plot of some data columns with user interface
elements to specify a mathematical model to fit to the model.
"""

from PyQt5 import uic, QtWidgets, QtCore
import pyqtgraph as pg
import pkg_resources
import numpy as np
import matplotlib.pyplot as plt
from lmfit import models
import asteval


NUM_POINTS = 1000
MSG_TIMEOUT = 5000


class VariableError(RuntimeError):
    pass


class PlotTab(QtWidgets.QWidget):
    """Tab widget containing plot with associated user interface.

    A widget containing a scatter plot of some data columns with user interface
    elements to specify a mathematical model to fit to the model.
    """

    x = None
    x_var = None
    y = None
    y_var = None
    x_err = None
    x_err_var = None
    y_err = None
    y_err_var = None
    err_width = None
    err_height = None
    fit = None
    fit_domain = None, None

    def __init__(self, data_model, main_window):
        """Initialize the widget.

        Args:
            data_model: the data model holding the data.
        """
        super().__init__()

        self.data_model = data_model
        uic.loadUi(
            pkg_resources.resource_stream("tailor.resources", "plot_tab.ui"), self
        )

        self.main_window = main_window

        self.param_layout = QtWidgets.QVBoxLayout()
        self.param_layout.setContentsMargins(4, 0, 0, 0)
        self.parameter_box.setLayout(self.param_layout)
        self._params = {}
        self._symbols = set(asteval.Interpreter().symtable.keys())

        # FIXME move this to create_plot, or vice versa?
        self._initial_param_plot = self.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="b", width=2)
        )
        self._fit_plot = self.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="r", width=2)
        )
        self.fit_domain_area = pg.LinearRegionItem(movable=True)

        # Set options affecting the UI
        self.fit_start_box.setOpts(
            value=-np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )
        self.fit_end_box.setOpts(
            value=np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )

        # Connect signals
        self.model_func.textEdited.connect(self.update_fit_params)
        self.show_initial_fit.stateChanged.connect(self.plot_initial_model)
        self.fit_start_box.sigValueChanging.connect(self.update_fit_domain)
        self.fit_end_box.sigValueChanging.connect(self.update_fit_domain)
        self.use_fit_domain.stateChanged.connect(self.toggle_use_fit_domain)
        self.fit_domain_area.sigRegionChanged.connect(self.fit_domain_region_changed)
        self.fit_button.clicked.connect(self.perform_fit)
        self.xlabel.textChanged.connect(self.update_xlabel)
        self.ylabel.textChanged.connect(self.update_ylabel)
        self.xmin.textEdited.connect(self.update_limits)
        self.xmax.textEdited.connect(self.update_limits)
        self.ymin.textEdited.connect(self.update_limits)
        self.ymax.textEdited.connect(self.update_limits)
        self.set_limits_button.clicked.connect(self.update_limits)

        self.plot_widget.setMenuEnabled(False)

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
        self.x_var = x_var
        self.y_var = y_var
        if x_err:
            self.x_err_var = x_err
        if y_err:
            self.y_err_var = y_err

        self.plot = self.plot_widget.plot(
            symbol="o",
            pen=None,
            symbolSize=5,
            symbolPen="k",
            symbolBrush="k",
        )
        self.error_bars = pg.ErrorBarItem()
        self.plot_widget.addItem(self.error_bars)
        self.update_function_label(y_var)
        self.xlabel.setText(x_var)
        self.ylabel.setText(y_var)

        self.update_plot()

        # set fit domain
        self.fit_start_box.setValue(self.x.min())
        self.fit_end_box.setValue(self.x.max())

    def update_plot(self):
        """Update plot to reflect any data changes."""
        self.update_data()

        # set data for scatter plot and error bars
        self.plot.setData(self.x, self.y)
        if self.x_err is not None:
            self.err_width = 2 * self.x_err
        if self.y_err is not None:
            self.err_height = 2 * self.y_err
        self.error_bars.setData(
            x=self.x, y=self.y, width=self.err_width, height=self.err_height
        )

        self.update_limits()

    def update_data(self):
        """Update data values from model."""
        self.x, self.y = self.data_model.get_columns([self.x_var, self.y_var])
        if self.x_err_var is not None:
            self.x_err = self.data_model.get_column(self.x_err_var)
        if self.y_err_var is not None:
            self.y_err = self.data_model.get_column(self.y_err_var)

    def update_xlabel(self):
        """Update the x-axis label of the plot."""
        self.plot_widget.setLabel("bottom", self.xlabel.text())
        self.main_window.statusbar.showMessage("Updated label.", msecs=MSG_TIMEOUT)

    def update_ylabel(self):
        """Update the y-axis label of the plot."""
        self.plot_widget.setLabel("left", self.ylabel.text())
        self.main_window.statusbar.showMessage("Updated label.", msecs=MSG_TIMEOUT)

    def update_limits(self):
        """Update the axis limits of the plot."""
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()
        self.plot_widget.setRange(xRange=(xmin, xmax), yRange=(ymin, ymax), padding=0)
        self.main_window.statusbar.showMessage("Updated limits.", msecs=MSG_TIMEOUT)

    def get_adjusted_limits(self):
        """Get adjusted plot limits from the data points and text fields.

        Return the minimum and maximum values of the data points, taking the
        error bars into account and adjust those values using the text fields
        for manual limits in the UI.

        Returns:
            Tuple of four float values (xmin, xmax, ymin, ymax).
        """
        xmin, xmax, ymin, ymax = self.get_limits_from_data()
        xmin = self.update_value_from_text(xmin, self.xmin)
        xmax = self.update_value_from_text(xmax, self.xmax)
        ymin = self.update_value_from_text(ymin, self.ymin)
        ymax = self.update_value_from_text(ymax, self.ymax)
        return xmin, xmax, ymin, ymax

    def get_limits_from_data(self, padding=0.05):
        """Get plot limits from the data points.

        Return the minimum and maximum values of the data points, taking the
        error bars into account.

        Args:
            padding: the relative amount of padding to add to the axis limits.
                Default is .05.

        Returns:
            Tuple of four float values (xmin, xmax, ymin, ymax).
        """
        if self.x_err is not None:
            x_err = self.x_err
        else:
            x_err = 0
        if self.y_err is not None:
            y_err = self.y_err
        else:
            y_err = 0

        xmin = min(self.x - x_err)
        xmax = max(self.x + x_err)
        ymin = min(self.y - y_err)
        ymax = max(self.y + y_err)

        xrange = xmax - xmin
        yrange = ymax - ymin

        xmin -= padding * xrange
        xmax += padding * xrange
        ymin -= padding * yrange
        ymax += padding * yrange

        return xmin, xmax, ymin, ymax

    def update_value_from_text(self, value, widget):
        """Update value from using a widget's text.

        Args:
            value: the original value, if update fails.
            widget: the widget containing the updated value.

        Returns:
            The updated value, or the original value if the update fails.
        """
        try:
            value = float(widget.text())
        except ValueError:
            pass
        return value

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
            self.main_window.statusbar.showMessage(
                "ERROR: " + str(exc), msecs=MSG_TIMEOUT
            )
            return
        else:
            old_params = set(self._params)
            self.add_params_to_ui(params - old_params)
            self.remove_params_from_ui(old_params - params)
            self.plot_initial_model()
            self.main_window.statusbar.showMessage("Updated model.", msecs=MSG_TIMEOUT)

    def get_params_from_model(self):
        """Get parameter names from the model function.

        Based on the mathematical expression for the model function, determine what are the parameters of the model.

        Raises VariableError when the dependent variable is part of the model function.

        Returns:
            A set of parameter names.
        """
        model_expr = self.model_func.text()
        code = compile(model_expr, "<string>", "eval")
        params = set(code.co_names) - set([self.x_var]) - self._symbols
        if self.y_var in params:
            raise VariableError(
                f"Dependent variable {self.y_var} must not be in function definition"
            )
        else:
            try:
                self.model = models.ExpressionModel(
                    model_expr, independent_vars=[self.x_var]
                )
            except ValueError as exc:
                raise VariableError(exc)
            return params

    def add_params_to_ui(self, params):
        """Add parameters to user interface.

        When the model function is changed and certain parameters are now part
        of the expression, they need to be added to the user interface.

        Args:
            params: a list of parameter names to add to the user interface.
        """
        for p in params:
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(QtWidgets.QLabel(f"{p}: "))
            min_box = pg.SpinBox(value=-np.inf, finite=False, compactHeight=False)
            min_box.setMaximumWidth(75)
            layout.addWidget(min_box)
            self._idx_min_value_box = layout.count() - 1
            layout.addWidget(QtWidgets.QLabel("≤"))
            value_box = pg.SpinBox(
                value=1.0,
                dec=True,
                step=0.1,
                minStep=0,
                finite=True,
                compactHeight=False,
            )
            value_box.sigValueChanging.connect(
                lambda: self.show_initial_fit.setChecked(True)
            )
            value_box.sigValueChanging.connect(self.plot_initial_model)
            value_box.setMaximumWidth(75)
            layout.addWidget(value_box)
            self._idx_value_box = layout.count() - 1
            layout.addWidget(QtWidgets.QLabel("≤"))
            max_box = pg.SpinBox(value=+np.inf, finite=False, compactHeight=False)
            max_box.setMaximumWidth(75)
            layout.addWidget(max_box)
            self._idx_max_value_box = layout.count() - 1
            layout.addWidget(QtWidgets.QCheckBox("Fixed"))
            self._idx_fixed_checkbox = layout.count() - 1

            self._params[p] = layout
            self.param_layout.addLayout(layout)

    def remove_params_from_ui(self, params):
        """Remove parameters from user interface.

        When the model function is changed and certain parameters are no longer
        part of the expression, remove them from the user interface.

        Args:
            params: a list of parameter names to remove from the user interface.
        """
        for p in params:
            layout = self._params[p]
            # delete all widgets from the parameter row
            for _ in range(layout.count()):
                item = layout.takeAt(0)
                item.widget().deleteLater()
            # remove and delete the parameter row
            self.param_layout.removeItem(layout)
            layout.deleteLater()
            # remove the reference to the parameter
            del self._params[p]

    def get_parameter_values(self):
        """Get current parameter values."""
        return {
            k: v.itemAt(self._idx_value_box).widget().value()
            for k, v in self._params.items()
        }

    def get_parameter_hints(self):
        """Get current parameter hints.

        Return not only the current value of parameters, but also the bounds and
        whether to vary the parameter or fix it.

        Returns:
            A dictionary with the parameter names as keys, and a tuple (min,
            value, max, fixed) as values.
        """
        return {
            k: (
                v.itemAt(self._idx_min_value_box).widget().value(),
                v.itemAt(self._idx_value_box).widget().value(),
                v.itemAt(self._idx_max_value_box).widget().value(),
                v.itemAt(self._idx_fixed_checkbox).widget().checkState(),
            )
            for k, v in self._params.items()
        }

    def toggle_use_fit_domain(self, state):
        """Enable or disable use of fit domain.

        Args:
            state: integer (enum Qt::CheckState) with the checkbox state.
        """
        if state == QtCore.Qt.Checked:
            self.plot_widget.addItem(self.fit_domain_area)
            self.update_fit_domain()
        else:
            self.plot_widget.removeItem(self.fit_domain_area)

    def fit_domain_region_changed(self):
        """Update the fit domain values.

        When the fit domain region is dragged by the user, the values in the
        start and end boxes need to be updated.
        """
        xmin, xmax = self.fit_domain_area.getRegion()
        self.fit_start_box.setValue(xmin)
        self.fit_end_box.setValue(xmax)

    def update_fit_domain(self):
        """Update the fit domain and indicate with vertical lines."""
        start = self.fit_start_box.value()
        end = self.fit_end_box.value()
        if start <= end:
            self.fit_domain = start, end
            self.fit_domain_area.setRegion((start, end))
        else:
            self.main_window.statusbar.showMessage(
                "ERROR: domain start is larger than end.", msecs=MSG_TIMEOUT
            )

    def plot_initial_model(self):
        """Plot model with initial parameters.

        Plots the model with the initial parameters as given in the user
        interface.
        """
        # FIXME Problem for constants like y = a
        x = np.linspace(min(self.x), max(self.x), NUM_POINTS)
        kwargs = self.get_parameter_values()
        kwargs[self.x_var] = x
        y = self.model.eval(**kwargs)

        if self.show_initial_fit.isChecked():
            self._initial_param_plot.setData(x, y)
        else:
            self._initial_param_plot.setData([], [])

    def perform_fit(self):
        """Perform fit and plot best fit model.

        Fits the model function to the data to estimate best fit parameters.
        When the fit is successful, the results are given in the result box and
        the best fit is plotted on top of the data.
        """
        # set model parameter hints
        param_hints = self.get_parameter_hints()
        for p, (min_, value, max_, is_fixed) in param_hints.items():
            self.model.set_param_hint(
                p, min=min_, value=value, max=max_, vary=not is_fixed
            )

        # select data for fit
        if self.use_fit_domain.checkState() == QtCore.Qt.Checked:
            xmin = self.fit_start_box.value()
            xmax = self.fit_end_box.value()
            if xmin > xmax:
                self.main_window.statusbar.showMessage(
                    "ERROR: domain start is larger than end.", msecs=MSG_TIMEOUT
                )
                return
            condition = (xmin <= self.x) & (self.x <= xmax)
            x = self.x[condition]
            y = self.y[condition]
            if self.y_err is not None:
                y_err = self.y_err[condition]
            else:
                y_err = None
        else:
            x = self.x
            y = self.y
            y_err = self.y_err

        # perform fit
        kwargs = {self.x_var: x}
        if y_err is not None:
            kwargs["weights"] = 1 / y_err
        self.fit = self.model.fit(y, **kwargs, nan_policy="omit")
        self.show_fit_results(self.fit)

        # plot best-fit model
        x = np.linspace(min(self.x), max(self.x), NUM_POINTS)
        y = self.fit.eval(**{self.x_var: x})
        self._fit_plot.setData(x, y)
        self.show_initial_fit.setChecked(False)

        self.main_window.statusbar.showMessage("Updated fit.", msecs=MSG_TIMEOUT)

    def show_fit_results(self, fit):
        """Show the results of the fit in the user interface.

        Args:
            fit: an lmfit.ModelResult object with the result of the fit.
        """
        results = make_header("Fit statistics")
        results += make_table([("# func. eval.", fit.nfev), ("red. chisq", fit.redchi)])

        results += "\n\n"
        results += make_header("Fit parameters")
        results += make_param_table(fit.params)

        self.result_box.setPlainText(results)

    def save_state_to_obj(self, save_obj):
        """Save all data and state to save object.

        Args:
            save_obj: a dictionary to store the data and state.
        """
        # save objects
        save_obj.update(
            {
                name: getattr(self, name)
                for name in [
                    "x_var",
                    "y_var",
                    "x_err_var",
                    "y_err_var",
                    "fit_domain",
                ]
            }
        )

        # save checkbox state
        save_obj.update(
            {
                name: getattr(self, name).checkState()
                for name in ["show_initial_fit", "use_fit_domain"]
            }
        )

        # save lineedit strings
        save_obj.update(
            {
                name: getattr(self, name).text()
                for name in [
                    "model_func",
                    "xlabel",
                    "xmin",
                    "xmax",
                    "ylabel",
                    "ymin",
                    "ymax",
                ]
            }
        )

        # save (possibly outdated) fit
        if self.fit.weights is not None:
            weights = self.fit.weights.to_list()
        else:
            weights = None
        saved_fit = {
            "model": self.fit.model.expr,
            "param_hints": self.fit.model.param_hints,
            "data": self.fit.data.to_list(),
            "weights": weights,
            "xdata": self.fit.userkws[self.x_var].to_list(),
        }
        save_obj["saved_fit"] = saved_fit

    def load_state_from_obj(self, save_obj):
        """Load all data and state from save object.

        Args:
            save_obj: a dictionary that contains the saved data and state.
        """
        self.create_plot(
            save_obj["x_var"],
            save_obj["y_var"],
            save_obj["x_err_var"],
            save_obj["y_err_var"],
        )

        start, end = save_obj["fit_domain"]
        self.fit_start_box.setValue(start)
        self.fit_end_box.setValue(end)

        # load linedit strings
        for name in [
            "model_func",
            "xlabel",
            "xmin",
            "xmax",
            "ylabel",
            "ymin",
            "ymax",
        ]:
            text = save_obj[name]
            widget = getattr(self, name)
            widget.setText(text)
            widget.textEdited.emit(text)

        # load checkbox state
        for name in ["show_initial_fit", "use_fit_domain"]:
            state = save_obj[name]
            getattr(self, name).setCheckState(state)

        # manually recreate (possibly outdated!) fit
        saved_fit = save_obj["saved_fit"]
        model = models.ExpressionModel(
            saved_fit["model"], independent_vars=[self.x_var]
        )

        for param, hint in saved_fit["param_hints"].items():
            model.set_param_hint(param, **hint)

        xdata = {save_obj["x_var"]: saved_fit["xdata"]}
        weights = saved_fit["weights"]
        if weights is not None:
            weights = np.array(weights)
        self.fit = model.fit(
            saved_fit["data"],
            **xdata,
            # weights MUST BE an NumPy array or calculations will fail
            weights=weights,
            nan_policy="omit",
        )

        self.show_fit_results(self.fit)

        # plot best-fit model
        x = np.linspace(min(self.x), max(self.x), NUM_POINTS)
        y = self.fit.eval(**{self.x_var: x})
        self._fit_plot.setData(x, y)

    def export_graph(self, filename):
        """Export graph to a file.

        Args:
            filename: path to the file.
        """
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()

        plt.figure()
        plt.errorbar(
            self.x,
            self.y,
            xerr=self.x_err,
            yerr=self.y_err,
            fmt="ko",
            ms=3,
            elinewidth=0.5,
        )
        if self.fit:
            x = np.linspace(min(self.x), max(self.x), NUM_POINTS)
            y = self.fit.eval(**{self.x_var: x})
            plt.plot(x, y, "r-")
        if self.use_fit_domain.isChecked():
            plt.axvspan(*self.fit_domain, facecolor="k", alpha=0.1)
        plt.xlabel(self.xlabel.text())
        plt.ylabel(self.ylabel.text())
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.savefig(filename)


def make_header(text):
    """Make header text with underlined with dashed."""
    return text + "\n" + len(text) * "-" + "\n"


def make_table(data):
    """Format numerical data in a table.

    Calculates the width of the first-column description texts and assumes numerical values for the second column and displays them with precision 4.

    Args:
        data: list of (text, value) tuples.
    """
    width = max([len(u[0]) for u in data])
    text = ""
    fmt = "{:" + str(width) + "s} = {:<9.4g}\n"
    for u, v in data:
        text += fmt.format(u, v)
    return text


def make_param_table(params):
    """Format parameter values in a table.

    Calculates the width of the first column based on parameter names. Formats the parameter values and uncertainties in a general format with precision 4.

    Args:
        params: a lmfit.Parameters object.
    """
    width = max([len(p) for p in params])
    text = ""
    fmt = "{:" + str(width) + "s} = {:< 10.4g} +/- {:< 10.4g}\n"
    for p in params:
        value = params[p].value
        stderr = params[p].stderr
        if stderr is None:
            stderr = 0
        text += fmt.format(p, value, stderr)
    return text
