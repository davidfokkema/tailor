"""Tab widget containing plot with associated user interface.

A widget containing a scatter plot of some data columns with user interface
elements to specify a mathematical model to fit to the model.
"""

from PyQt5 import uic, QtWidgets, QtCore
import pyqtgraph as pg
import pkg_resources
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lmfit import models
import asteval


NUM_POINTS = 1000
MSG_TIMEOUT = 0

DRAW_CURVE_ON_DATA = 0
DRAW_CURVE_ON_DOMAIN = 1
DRAW_CURVE_ON_AXIS = 2
DRAW_CURVE_OPTIONS = ["On data points", "Only on fit domain", "On full axis"]


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
    model = None

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
            symbol=None, pen=pg.mkPen(color="00F4", width=4)
        )
        self._fit_plot = self.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="r", width=4)
        )
        self.fit_domain_area = pg.LinearRegionItem(movable=True, brush="00F1")

        # Set options affecting the UI
        self.fit_start_box.setOpts(
            value=-np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )
        self.fit_end_box.setOpts(
            value=np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )
        self.fit_start_box.setMaximumWidth(75)
        self.fit_end_box.setMaximumWidth(75)
        self.draw_curve_option.addItems(DRAW_CURVE_OPTIONS)
        # lambda is necessary to gobble the 'index' parameter of the
        # currentIndexChanged signal
        self.draw_curve_option.currentIndexChanged.connect(
            lambda index: self.update_best_fit_plot()
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
        self.plot_widget.sigXRangeChanged.connect(self.updated_plot_range)

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
        self.update_info_box()

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
        x, y = self.data_model.get_columns([self.x_var, self.y_var])
        if self.x_err_var is not None:
            x_err = self.data_model.get_column(self.x_err_var)
        else:
            x_err = 0
        if self.y_err_var is not None:
            y_err = self.data_model.get_column(self.y_err_var)
        else:
            y_err = 0

        # Drop NaN and Inf values
        df = pd.DataFrame.from_dict({"x": x, "y": y, "x_err": x_err, "y_err": y_err})
        df.dropna(inplace=True)
        self.x, self.y, self.x_err, self.y_err = df.to_numpy().T

    def update_xlabel(self):
        """Update the x-axis label of the plot."""
        self.plot_widget.setLabel("bottom", self.xlabel.text())
        self.main_window.statusbar.showMessage("Updated label.", msecs=MSG_TIMEOUT)

    def update_ylabel(self):
        """Update the y-axis label of the plot."""
        self.plot_widget.setLabel("left", self.ylabel.text())
        self.main_window.statusbar.showMessage("Updated label.", msecs=MSG_TIMEOUT)

    def update_info_box(self):
        """Update the information box."""
        msgs = []
        if self.fit:
            msgs.append(self.format_fit_results())
        msgs.append(self.format_plot_info())
        self.result_box.setPlainText("\n".join(msgs))

    def update_limits(self):
        """Update the axis limits of the plot."""
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()
        # BUGFIX:
        # disableAutoRange=False is necessary to prevent triggering a ranging
        # bug for large y-values (> 1e6)
        # However, that will break setting the axis limits manually. Setting to
        # True for now.
        self.plot_widget.setRange(
            xRange=(xmin, xmax), yRange=(ymin, ymax), padding=0, disableAutoRange=True
        )
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
            params = self.get_params_and_update_model()
        except (SyntaxError, VariableError) as exc:
            self.main_window.statusbar.showMessage(f"ERROR: {exc!s}", msecs=MSG_TIMEOUT)
            self.model = None
        else:
            self.update_params_ui(params)
            self.plot_initial_model()
            self.main_window.statusbar.showMessage("Updated model.", msecs=MSG_TIMEOUT)

    def update_params_ui(self, params):
        """Add and/or remove parameters if necessary.

        Args:
            params: list of parameter names which should be in the user interface.
        """
        old_params = set(self._params)
        self.add_params_to_ui(params - old_params)
        self.remove_params_from_ui(old_params - params)

    def get_params_and_update_model(self):
        """Get parameter names and update the model function.

        Based on the mathematical expression for the model function, determine
        what are the parameters of the model. If the model compiles, the model
        object is updated as well.

        Raises VariableError when the dependent variable is part of the model
        function.

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
            layout.addWidget(QtWidgets.QLabel(f"{p}: ", minimumWidth=30))
            min_box = pg.SpinBox(value=-np.inf, finite=False, compactHeight=False)
            min_box.setMaximumWidth(75)
            layout.addWidget(min_box)
            self._idx_min_value_box = layout.count() - 1
            layout.addWidget(
                QtWidgets.QLabel(
                    "≤", alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
                )
            )
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
            layout.addWidget(
                QtWidgets.QLabel(
                    "≤", alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
                )
            )
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
            k: {
                "min": v.itemAt(self._idx_min_value_box).widget().value(),
                "value": v.itemAt(self._idx_value_box).widget().value(),
                "max": v.itemAt(self._idx_max_value_box).widget().value(),
                "vary": not v.itemAt(self._idx_fixed_checkbox).widget().checkState(),
            }
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
        self.update_best_fit_plot()

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
        if self.model is None:
            self.main_window.statusbar.showMessage(
                "FIT FAILED: please fix your model first."
            )
            return

        # set model parameter hints
        param_hints = self.get_parameter_hints()
        for p, hints in param_hints.items():
            self.model.set_param_hint(p, **hints)

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
            if self.y_err_var is not None:
                y_err = self.y_err[condition]
            else:
                y_err = None
        else:
            x = self.x
            y = self.y
            if self.y_err_var is not None:
                y_err = self.y_err
            else:
                y_err = None

        # perform fit
        kwargs = {self.x_var: x}
        if y_err is not None:
            kwargs["weights"] = 1 / y_err
        try:
            self.fit = self.model.fit(y, **kwargs, nan_policy="omit")
        except Exception as exc:
            self.main_window.statusbar.showMessage(f"FIT FAILED: {exc}")
        else:
            self.update_info_box()
            self.update_best_fit_plot()
            self.show_initial_fit.setChecked(False)
            self.main_window.statusbar.showMessage("Updated fit.", msecs=MSG_TIMEOUT)

    def updated_plot_range(self):
        """Handle updated plot range.

        If the fitted curves are drawn on the full axis, they need to be updated
        when the plot range is changed.
        """
        if self.draw_curve_option.currentIndex() == DRAW_CURVE_ON_AXIS:
            self.update_best_fit_plot()

    def update_best_fit_plot(self, x_var=None):
        """Update the plot of the best-fit model curve.

        Args:
            x_var: optional name of the x-variable to use for the model. Only
                useful for loading project files which have an outdated fit object
                with an outdated x-variable name (i.e. shortly after renaming a
                column and not updating the model function).
        """
        if self.fit:
            if x_var is None:
                x_var = self.x_var
            xmin, xmax = self.get_fit_curve_x_limits()
            x = np.linspace(xmin, xmax, NUM_POINTS)
            y = self.fit.eval(**{x_var: x})
            self._fit_plot.setData(x, y)

    def get_fit_curve_x_limits(self):
        """Get x-axis limits for fit curve.

        This method respects the choice in the 'Draw curve' option box.

        Returns:
            xmin, xmax: tuple of floats with the x-axis limits
        """
        option_idx = self.draw_curve_option.currentIndex()
        if option_idx == DRAW_CURVE_ON_DATA:
            xmin, xmax = min(self.x), max(self.x)
        elif option_idx == DRAW_CURVE_ON_DOMAIN:
            xmin, xmax = self.fit_domain
        elif option_idx == DRAW_CURVE_ON_AXIS:
            [[xmin, xmax], _] = self.plot_widget.viewRange()
        else:
            raise NotImplementedError(
                f"Draw curve option {option_idx} not implemented."
            )
        return xmin, xmax

    def format_plot_info(self):
        """Format basic plot information in the results box.

        Returns:
            A string containing the formatted plot information.
        """
        msg = make_header("Data sources")
        msg += make_table(
            [
                # make sure everything is a string, even None
                ("X: ", str(self.x_var), " +- ", str(self.x_err_var)),
                ("Y: ", str(self.y_var), " +- ", str(self.y_err_var)),
            ]
        )
        return msg

    def format_fit_results(self):
        """Format the results of the fit in the user interface.

        Returns:
            A string containing the formatted fit results.
        """
        msg = make_header("Fit statistics")
        msg += make_table(
            [
                ("function evaluations", " = ", f"{self.fit.nfev:<9.4g}"),
                ("reduced chisquare", " = ", f"{self.fit.redchi:<9.4g}"),
                ("degrees of freedom", " = ", f"{self.fit.nfree:<9.4g}"),
            ]
        )

        msg += "\n\n"
        msg += make_header("Fit parameters")
        msg += make_param_table(self.fit.params)

        return msg

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

        # save combobox state
        save_obj.update(
            {name: getattr(self, name).currentIndex() for name in ["draw_curve_option"]}
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

        save_obj["parameters"] = self.get_parameter_hints()

        # save (possibly outdated) fit
        if self.fit:
            if self.fit.weights is not None:
                weights = list(self.fit.weights)
            else:
                weights = None
            x_var = self.fit.model.independent_vars[0]
            saved_fit = {
                "model": self.fit.model.expr,
                "param_hints": self.fit.model.param_hints,
                "data": list(self.fit.data),
                "weights": weights,
                "x_var": x_var,
                "xdata": list(self.fit.userkws[x_var]),
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
        for name in ["use_fit_domain"]:
            state = save_obj[name]
            getattr(self, name).setCheckState(state)

        # load combobox state
        for name in ["draw_curve_option"]:
            state = save_obj[name]
            getattr(self, name).setCurrentIndex(state)

        # set parameter hints
        params = save_obj["parameters"].keys()
        self.update_params_ui(params)
        for p, hints in save_obj["parameters"].items():
            if hints["vary"]:
                fixed_state = QtCore.Qt.Unchecked
            else:
                fixed_state = QtCore.Qt.Checked
            layout = self._params[p]
            layout.itemAt(self._idx_min_value_box).widget().setValue(hints["min"])
            layout.itemAt(self._idx_value_box).widget().setValue(hints["value"])
            layout.itemAt(self._idx_max_value_box).widget().setValue(hints["max"])
            layout.itemAt(self._idx_fixed_checkbox).widget().setCheckState(fixed_state)

        # manually recreate (possibly outdated!) fit
        if "saved_fit" in save_obj:
            saved_fit = save_obj["saved_fit"]

            # workaround for older projects which did not explicitly store the
            # fit objects x-variable
            if "x_var" in saved_fit:
                x_var = saved_fit["x_var"]
            else:
                x_var = self.x_var

            model = models.ExpressionModel(saved_fit["model"], independent_vars=[x_var])

            for param, hint in saved_fit["param_hints"].items():
                model.set_param_hint(param, **hint)

            xdata = {x_var: saved_fit["xdata"]}
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

            self.update_info_box()
            self.update_best_fit_plot(x_var)

        # set state of show_initial_fit, will have changed when setting parameters
        self.show_initial_fit.setCheckState(save_obj["show_initial_fit"])

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
            fit_xmin, fit_xmax = self.get_fit_curve_x_limits()
            x = np.linspace(fit_xmin, fit_xmax, NUM_POINTS)
            y = self.fit.eval(**{self.x_var: x})
            plt.plot(x, y, "r-")
        if self.use_fit_domain.isChecked():
            plt.axvspan(*self.fit_domain, facecolor="k", alpha=0.1)
        plt.xlabel(self.xlabel.text())
        plt.ylabel(self.ylabel.text())
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.savefig(filename, dpi=300)


def make_header(text):
    """Make header text with underlined with dashed.

    Returns:
        A string with the formatted header text.
    """
    return text + "\n" + len(text) * "-" + "\n"


def make_table(data):
    """Format data in a table.

    Calculates the width of the column texts to lay out the table. All values must be passed as string to make the layout work correctly.

    Args:
        data: list of (text1, text2, ...) tuples of string values.

    Returns:
        A string with the formatted table text.
    """
    cols = zip(*data)
    widths = [max([len(row) for row in col]) for col in cols]
    table = ""
    for row in data:
        for txt, col_width in zip(row, widths):
            fmt = f"{{:{col_width}s}}"
            table += fmt.format(txt)
        table += "\n"
    return table


def make_param_table(params):
    """Format parameter values in a table.

    Calculates the width of the first column based on parameter names. Formats the parameter values and uncertainties in a general format with precision 4.

    Args:
        params: a lmfit.Parameters object.

    Returns:
        A string with the formatted table text.
    """
    width = max([len(p) for p in params])
    text = ""
    fmt = "{:" + str(width) + "s} = {:< 12.6g} +/- {:< 12.6g} ({:s} %)\n"
    for p in params:
        value = params[p].value
        stderr = params[p].stderr
        if stderr is None:
            stderr = 0
        try:
            rel_err = "{:.1f}".format(abs(stderr / value * 100))
        except ZeroDivisionError:
            rel_err = "--"
        text += fmt.format(p, value, stderr, rel_err)
    return text
