"""Tab widget containing plot with associated user interface.

A widget containing a scatter plot of some data columns with user interface
elements to specify a mathematical model to fit to the model.
"""

import enum
import functools

import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from tailor.data_sheet import DataSheet
from tailor.plot_model import PlotModel
from tailor.ui_plot_tab import Ui_PlotTab

NUM_POINTS = 1000
MSG_TIMEOUT = 0


DrawCurve = enum.IntEnum("DrawCurve", ["ON_DATA", "ON_DOMAIN", "ON_AXIS"])
DRAW_CURVE_OPTIONS = {
    DrawCurve.ON_DATA: "On data points",
    DrawCurve.ON_DOMAIN: "Only on fit domain",
    DrawCurve.ON_AXIS: "On full axis",
}


class VariableError(RuntimeError):
    pass


class PlotTab(QtWidgets.QWidget):
    """Tab widget containing plot with associated user interface.

    A widget containing a scatter plot of some data columns with user interface
    elements to specify a mathematical model to fit to the model.
    """

    name: str
    id: int
    data_sheet: DataSheet
    model: PlotModel
    _params: dict[str, QtWidgets.QWidget]
    _cursor_pos: int = 0

    def __init__(
        self,
        name: str,
        id: int,
        data_sheet: DataSheet,
        x_col: str,
        y_col: str,
        x_err_col: str | None = None,
        y_err_col: str | None = None,
    ) -> None:
        """Initialize the widget.

        Args:
            data_sheet: the data sheet holding the data.
        """
        super().__init__()
        self.ui = Ui_PlotTab()
        self.ui.setupUi(self)

        self.name = name
        self.id = id
        self.model = PlotModel(
            data_sheet.model.data_model, x_col, y_col, x_err_col, y_err_col
        )
        self.data_sheet = data_sheet
        self._params = {}

        self.create_plot()
        self.connect_ui_events()
        self.finish_ui()

    def __repr__(self) -> None:
        return f"PlotTab(id={self.id}, name={self.name})"

    def connect_ui_events(self):
        # Connect signals
        self.ui.model_func.textChanged.connect(self.update_model_expression)
        self.ui.model_func.cursorPositionChanged.connect(self.store_cursor_position)
        self.ui.show_initial_fit.stateChanged.connect(self.plot_initial_model)
        self.ui.fit_start_box.sigValueChanging.connect(self.update_fit_domain_xmin)
        self.ui.fit_end_box.sigValueChanging.connect(self.update_fit_domain_xmax)
        self.ui.use_fit_domain.stateChanged.connect(self.set_use_fit_domain)
        self.fit_domain_area.sigRegionChanged.connect(self.fit_domain_region_changed)
        self.ui.xlabel.textChanged.connect(self.update_xlabel)
        self.ui.ylabel.textChanged.connect(self.update_ylabel)
        self.ui.x_min.textChanged.connect(self.update_x_min)
        self.ui.x_max.textChanged.connect(self.update_x_max)
        self.ui.y_min.textChanged.connect(self.update_y_min)
        self.ui.y_max.textChanged.connect(self.update_y_max)
        self.ui.set_limits_button.clicked.connect(self.update_limits)
        self.ui.fit_button.clicked.connect(self.perform_fit)
        self.ui.plot_widget.sigXRangeChanged.connect(self.updated_plot_range)
        # # lambda is necessary to gobble the 'index' parameter of the
        # # currentIndexChanged signal
        self.ui.draw_curve_option.currentIndexChanged.connect(self.update_model_curves)

    def finish_ui(self):
        self.ui.param_layout = QtWidgets.QVBoxLayout()
        self.ui.param_layout.setContentsMargins(4, 0, 0, 0)
        self.ui.param_layout.setSpacing(0)
        # add stretch to prevent excessive widget sizes for small numbers of
        # parameters
        self.ui.param_layout.addStretch()
        self.ui.parameter_list.setLayout(self.ui.param_layout)

        # Set options affecting the UI
        self.ui.fit_start_box.setOpts(
            value=-np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )
        self.ui.fit_end_box.setOpts(
            value=np.inf, dec=True, step=0.1, finite=True, compactHeight=False
        )
        self.ui.fit_start_box.setMaximumWidth(75)
        self.ui.fit_end_box.setMaximumWidth(75)
        self.ui.draw_curve_option.addItems(DRAW_CURVE_OPTIONS.values())

        self.ui.plot_widget.setMenuEnabled(False)
        self.ui.plot_widget.hideButtons()

    def create_plot(self):
        """Create a plot in the widget.

        Create a plot from data in the columns specified by the given column
        names.
        """
        self.plot = self.ui.plot_widget.plot(
            symbol="o",
            pen=None,
            symbolSize=5,
            symbolPen="k",
            symbolBrush="k",
        )
        self.error_bars = pg.ErrorBarItem()
        self.ui.plot_widget.addItem(self.error_bars)
        self.initial_param_plot = self.ui.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="#DDF", width=4)
        )
        self.fit_plot = self.ui.plot_widget.plot(
            symbol=None, pen=pg.mkPen(color="#00F", width=4)
        )
        self.fit_domain_area = pg.LinearRegionItem(movable=True, brush="#00F1")

        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        self.ui.plot_widget.setLabel("left", self.model.y_label)

    def refresh_ui(self):
        """Refresh UI after switching tabs.

        When the plot tab becomes visible again, update all data and
        information. Explicitly refresh all things that may have changed: the
        model (x-axis name change), plot curves and info box (x- and y-axis name
        changes) and possibly invalidated best fit. Because changes are
        propagated this may actually result in certain methods being called
        multiple times. Since this only happens on tab switches, we don't
        optimize that away to keep the code simple.
        """
        self.update_model_widget()
        self.update_axis_settings_from_model()
        self.update_plot()
        self.model.verify_best_fit_data()
        self.update_params_ui_values_from_model()
        self.update_fit_domain_from_model()
        self.update_model_curves()
        self.update_info_box()

    def change_data_source(
        self,
        data_sheet: DataSheet,
        x_col_name: str,
        y_col_name: str,
        x_err_col_name: str | None = None,
        y_err_col_name: str | None = None,
    ) -> None:
        """Change data source of the plot.

        This method will let you change the sheet containing the underlying data, but also change the axes or error bars to other data columns. The model expression is left unchanged. That is, if you had something like `a * x + b` and your x-axis is now called `t`, you'll have to manually update the model expression.

        Args:
            data_sheet (DataSheet): the new data sheet containing the data.
            x_col_name (str): the new x column name.
            y_col_name (str): the new y column name.
            x_err_col_name (str | None, optional): the new x error column name.
                Defaults to None.
            y_err_col_name (str | None, optional): the new y error column name.
                Defaults to None.
        """
        # Save model expression using variable names. This is necessary because
        # the model is stored using column labels like col1, col2, etc. If you
        # change plot sources, you want the 'x' in your model to point to the
        # 'x' column in the data, not 'col1' to 'col1', which might be something
        # different on another data sheet.
        current_model = self.model.get_model_expression()

        # change data source
        self.data_sheet = data_sheet
        self.model.data_model = data_sheet.model.data_model
        self.model.x_col = self.model.data_model.get_column_label_by_name(x_col_name)
        self.model.y_col = self.model.data_model.get_column_label_by_name(y_col_name)
        self.model.x_err_col = (
            self.model.data_model.get_column_label_by_name(x_err_col_name)
            if x_err_col_name
            else None
        )
        self.model.y_err_col = (
            self.model.data_model.get_column_label_by_name(y_err_col_name)
            if y_err_col_name
            else None
        )

        # restore model expression using variable names
        self.model.update_model_expression(current_model)
        # refresh the plot UI
        self.refresh_ui()

    def get_draw_curve_option(self) -> DrawCurve:
        """Get the currently selected draw curve option.

        Returns:
            DrawCurve: the currently selected option
        """
        option_idx = self.ui.draw_curve_option.currentIndex()
        options = list(DRAW_CURVE_OPTIONS.keys())
        return options[option_idx]

    def update_model_widget(self):
        """Update function label."""
        variable = self.model.get_y_col_name()
        new_label_text = f"Function: {variable} ="
        self.ui.model_func_label.setText(new_label_text)
        cursor_pos = self._cursor_pos
        self.ui.model_func.setPlainText(self.model.get_model_expression())
        # cursor is reset after setting text
        cursor = self.ui.model_func.textCursor()
        cursor.setPosition(cursor_pos)
        self.ui.model_func.setTextCursor(cursor)
        self.update_expression_border()

    def update_axis_settings_from_model(self) -> None:
        """Update axis labels from model."""
        self.ui.xlabel.setText(self.model.x_label)
        self.ui.ylabel.setText(self.model.y_label)
        self.ui.x_min.setText("" if self.model.x_min is None else str(self.model.x_min))
        self.ui.x_max.setText("" if self.model.x_max is None else str(self.model.x_max))
        self.ui.y_min.setText("" if self.model.y_min is None else str(self.model.y_min))
        self.ui.y_max.setText("" if self.model.y_max is None else str(self.model.y_max))

    def update_plot(self):
        """Update plot to reflect any data changes."""

        # x_err, y_err will be 0.0 if no errors are specified
        x, y, x_err, y_err = self.model.get_data()

        # set data for scatter plot and error bars
        self.plot.setData(x, y)
        err_width = 2 * x_err
        err_height = 2 * y_err
        self.error_bars.setData(x=x, y=y, width=err_width, height=err_height)

        self.update_limits()

    def update_info_box(self):
        """Update the information box."""
        msgs = []
        if self.model.best_fit is not None:
            msgs.append(self.format_fit_results())
        msgs.append(self.format_plot_info())
        self.ui.result_box.setPlainText("\n".join(msgs))

    def update_xlabel(self):
        """Update the x-axis label of the plot."""
        self.model.x_label = self.ui.xlabel.text()
        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        # FIXME self.main_window.ui.statusbar.showMessage("Updated label.", timeout=MSG_TIMEOUT)

    def update_ylabel(self):
        """Update the y-axis label of the plot."""
        self.model.y_label = self.ui.ylabel.text()
        self.ui.plot_widget.setLabel("left", self.model.y_label)
        # FIXME self.main_window.ui.statusbar.showMessage("Updated label.", timeout=MSG_TIMEOUT)

    def update_x_min(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.x_min.text())
        except ValueError:
            value = None
        self.model.x_min = value
        self.update_limits()

    def update_x_max(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.x_max.text())
        except ValueError:
            value = None
        self.model.x_max = value
        self.update_limits()

    def update_y_min(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.y_min.text())
        except ValueError:
            value = None
        self.model.y_min = value
        self.update_limits()

    def update_y_max(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.y_max.text())
        except ValueError:
            value = None
        self.model.y_max = value
        self.update_limits()

    def update_limits(self):
        """Update the axis limits of the plot."""
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()
        # BUGFIX:
        # disableAutoRange=False is necessary to prevent triggering a ranging
        # bug for large y-values (> 1e6)
        # However, that will break setting the axis limits manually. Setting to
        # True for now.
        self.ui.plot_widget.setRange(
            xRange=(xmin, xmax), yRange=(ymin, ymax), padding=0, disableAutoRange=True
        )
        # FIXME
        # self.main_window.ui.statusbar.showMessage(
        #     "Updated limits.", timeout=MSG_TIMEOUT
        # )

    def get_adjusted_limits(self):
        """Get adjusted plot limits from the data points and text fields.

        Return the minimum and maximum values of the data points, taking the
        error bars into account but override with any limits specified.

        Returns:
            Tuple of four float values (xmin, xmax, ymin, ymax).
        """
        x_min, x_max, y_min, y_max = self.model.get_limits_from_data()
        x_min = x_min if self.model.x_min is None else self.model.x_min
        x_max = x_max if self.model.x_max is None else self.model.x_max
        y_min = y_min if self.model.y_min is None else self.model.y_min
        y_max = y_max if self.model.y_max is None else self.model.y_max
        return x_min, x_max, y_min, y_max

    def update_model_expression(self):
        """Update the model expression and related UI."""
        expression = self.ui.model_func.toPlainText()
        self.model.update_model_expression(expression)
        self.update_expression_border()
        self.update_params_ui()
        self.plot_initial_model()
        self.plot_best_fit()

    def update_expression_border(self) -> None:
        """Update border of the model expression widget.

        If the model expression is not valid, draw a red border around the
        widget.
        """
        if self.model.is_model_valid():
            self.ui.model_func.setStyleSheet("border: 0px")
        else:
            self.ui.model_func.setStyleSheet("border: 1px solid red")

    def store_cursor_position(self):
        """Store the cursor position inside the model expression."""
        self._cursor_pos = self.ui.model_func.textCursor().position()

    def update_params_ui(self):
        """Add and/or remove parameters if necessary."""
        old_params = set(self._params)
        current_params = set(self.model.get_parameter_names())
        self.add_params_to_ui(current_params - old_params)
        self.remove_params_from_ui(old_params - current_params)

    def add_params_to_ui(self, params):
        """Add parameters to user interface.

        When the model function is changed and certain parameters are now part
        of the expression, they need to be added to the user interface.

        Args:
            params: a list of parameter names to add to the user interface.
        """
        for param in params:
            # create widgets
            label = QtWidgets.QLabel(f"{param}: ", minimumWidth=30)
            value_box = pg.SpinBox(
                value=1.0,
                dec=True,
                step=0.1,
                minStep=0,
                finite=True,
                compactHeight=False,
            )
            value_box.setObjectName("value")
            value_box._parameter = param
            min_box = pg.SpinBox(value=-np.inf, finite=False, compactHeight=False)
            min_box.setObjectName("min")
            min_box._parameter = param
            max_box = pg.SpinBox(value=+np.inf, finite=False, compactHeight=False)
            max_box.setObjectName("max")
            max_box._parameter = param
            is_fixed_checkbox = QtWidgets.QCheckBox("Fixed", objectName="is_fixed")
            is_fixed_checkbox._parameter = param
            create_leq_sign = lambda: QtWidgets.QLabel(
                "≤", alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter
            )

            # connect signals to changes in parameter values or bounds
            value_box.sigValueChanging.connect(self.update_parameter_value)
            min_box.sigValueChanging.connect(self.update_parameter_min_bound)
            max_box.sigValueChanging.connect(self.update_parameter_max_bound)
            is_fixed_checkbox.stateChanged.connect(
                functools.partial(self.update_parameter_fixed_state, is_fixed_checkbox)
            )

            # build parameter layout
            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(min_box)
            layout.addWidget(create_leq_sign())
            layout.addWidget(value_box)
            layout.addWidget(create_leq_sign())
            layout.addWidget(max_box)
            layout.addWidget(is_fixed_checkbox)
            layout.setSpacing(12)
            value_box.setMaximumWidth(75)
            min_box.setMaximumWidth(75)
            max_box.setMaximumWidth(75)
            layout.setContentsMargins(0, 0, 0, 0)

            # put layout into widget
            layout_widget = QtWidgets.QWidget()
            layout_widget.setLayout(layout)

            # store parameter layout
            self._params[param] = layout_widget
            # determine position to insert the parameter in alphabetical order
            sorted_params = sorted(list(self._params.keys()))
            idx = sorted_params.index(param)
            self.ui.param_layout.insertWidget(idx, layout_widget)

    def remove_params_from_ui(self, params):
        """Remove parameters from user interface.

        When the model function is changed and certain parameters are no longer
        part of the expression, remove them from the user interface.

        Args:
            params: a list of parameter names to remove from the user interface.
        """
        for param in params:
            layout_widget = self._params.pop(param)
            self.ui.param_layout.removeWidget(layout_widget)
            layout_widget.deleteLater()

    def update_parameter_value(self, widget, value):
        self.model.set_parameter_value(widget._parameter, value)
        self.update_model_curves()

    def update_parameter_min_bound(self, widget, value):
        self.model.set_parameter_min_value(widget._parameter, value)
        self.update_model_curves()

    def update_parameter_max_bound(self, widget, value):
        self.model.set_parameter_max_value(widget._parameter, value)
        self.update_model_curves()

    def update_parameter_fixed_state(self, widget, fixed_state):
        print("CALLED")
        vary_state = not fixed_state
        self.model.set_parameter_vary_state(widget._parameter, vary_state)
        self.update_model_curves()

    def update_params_ui_values_from_model(self):
        """Update the parameters UI to sync with model.

        Changed parameter values in the UI will propagate to the PlotModel
        instance managing all plot data, but you will need to call this method
        to propagate changed model values back to the UI.

        This method expects that all model parameters already exist within the
        UI.
        """
        for name in self.model.get_parameter_names():
            parameter = self.model.get_parameter_by_name(name)
            widget = self._params[parameter.name]
            for w in widget.findChildren(QtWidgets.QWidget):
                w.blockSignals(True)
            widget.findChild(QtWidgets.QWidget, "min").setValue(parameter.min)
            widget.findChild(QtWidgets.QWidget, "value").setValue(parameter.value)
            widget.findChild(QtWidgets.QWidget, "max").setValue(parameter.max)
            widget.findChild(QtWidgets.QWidget, "is_fixed").setChecked(
                not parameter.vary
            )
            for w in widget.findChildren(QtWidgets.QWidget):
                w.blockSignals(False)

    def set_use_fit_domain(self, state):
        """Enable or disable use of fit domain.

        Args:
            state: integer (enum Qt::CheckState) with the checkbox state.
        """
        if state == QtCore.Qt.Checked.value:
            self.model.set_fit_domain_enabled(True)
            self.ui.plot_widget.addItem(self.fit_domain_area)
        else:
            self.model.set_fit_domain_enabled(False)
            self.ui.plot_widget.removeItem(self.fit_domain_area)
        self.update_model_curves()

    def fit_domain_region_changed(self):
        """Update the fit domain values.

        When the fit domain region is dragged by the user, the values in the
        start and end boxes need to be updated.
        """
        xmin, xmax = self.fit_domain_area.getRegion()
        self.ui.fit_start_box.setValue(xmin)
        self.ui.fit_end_box.setValue(xmax)

    def update_fit_domain_xmin(self, widget, xmin: float) -> None:
        """Update fit domain lower bound.

        Update the lower bound of the fit domain in the model and update the
        shaded region in the plot. If the lower bound is greater than the upper
        bound, the upper bound is pushed to the right and both bounds are equal.

        Args:
            widget (Any): the spinbox widget (ignored).
            xmin (float): the new value for the lower bound.
        """
        xmax = self.ui.fit_end_box.value()
        if xmax < xmin:
            xmax = xmin
            self.ui.fit_end_box.setValue(xmax)
        self.model.set_fit_domain(xmin=xmin, xmax=xmax)
        self.fit_domain_area.blockSignals(True)
        self.fit_domain_area.setRegion((xmin, xmax))
        self.fit_domain_area.blockSignals(False)
        self.update_model_curves()

    def update_fit_domain_xmax(self, widget, xmax: float) -> None:
        """Update fit domain upper bound.

        Update the upper bound of the fit domain in the model and update the
        shaded region in the plot. If the upper bound is smaller than the lower
        bound, the lower bound is pushed to the left and both bounds are equal.

        Args:
            widget (Any): the spinbox widget (ignored).
            xmin (float): the new value for the upper bound.
        """
        xmin = self.ui.fit_start_box.value()
        if xmin > xmax:
            xmin = xmax
            self.ui.fit_start_box.setValue(xmin)
        self.model.set_fit_domain(xmin=xmin, xmax=xmax)
        self.fit_domain_area.blockSignals(True)
        self.fit_domain_area.setRegion((xmin, xmax))
        self.fit_domain_area.blockSignals(False)
        self.update_model_curves()

    def update_fit_domain_from_model(self) -> None:
        """Update fit domain parameters from model.

        Update the fit domain UI widgets with values taken from the plot model.
        Makes sure signals are not unnecessarily triggered which would result in
        invalidating the best fit. The best fit is preserved by this method.
        """
        self.ui.fit_start_box.blockSignals(True)
        self.ui.fit_end_box.blockSignals(True)
        xmin, xmax = self.model.get_fit_domain()
        self.ui.fit_start_box.setValue(xmin)
        self.ui.fit_end_box.setValue(xmax)
        if self.model.get_fit_domain_enabled():
            state = QtCore.Qt.CheckState.Checked
        else:
            state = QtCore.Qt.CheckState.Unchecked
        self.ui.use_fit_domain.setCheckState(state)
        self.fit_domain_area.setRegion((xmin, xmax))
        self.ui.fit_start_box.blockSignals(False)
        self.ui.fit_end_box.blockSignals(False)

    def update_model_curves(self):
        """Update initial and best fit curves."""
        self.plot_initial_model()
        self.plot_best_fit()

    def updated_plot_range(self):
        """Handle updated plot range.

        If the fitted curves are drawn on the full axis, they need to be updated
        when the plot range is changed.
        """
        if self.get_draw_curve_option() == DrawCurve.ON_AXIS:
            self.update_model_curves()

    def plot_initial_model(self):
        """Plot model with initial parameters.

        Plots the model with the initial parameters as given in the user
        interface.
        """
        if self.ui.show_initial_fit.isChecked():
            x_min, x_max = self.get_fit_curve_x_limits()
            x = np.linspace(x_min, x_max, NUM_POINTS)
            y = self.model.evaluate_model(x)
            if y is not None:
                self.initial_param_plot.setData(x, y)
                return
        # in all other cases: reset data
        self.initial_param_plot.setData([], [])

    def perform_fit(self):
        self.model.perform_fit()
        self.plot_best_fit()
        self.update_info_box()

    def plot_best_fit(self):
        """Update the plot of the best-fit model curve.

        Plots the model with the best fit parameters if they are previously
        determined by performing a fit.
        """
        x_min, x_max = self.get_fit_curve_x_limits()
        x = np.linspace(x_min, x_max, NUM_POINTS)
        y = self.model.evaluate_best_fit(x)
        if y is not None:
            self.fit_plot.setData(x, y)
            self.fit_plot.setPen(color="b", width=4)
        else:
            # colour outdated fit plot light red
            self.fit_plot.setPen(color="#FBB", width=4)

    def get_fit_curve_x_limits(self):
        """Get x-axis limits for fit curve.

        This method respects the choice in the 'Draw curve' option box.

        Returns:
            x_min, x_max: tuple of floats with the x-axis limits
        """
        option = self.get_draw_curve_option()
        if option == DrawCurve.ON_DATA:
            x_min, x_max, _, _ = self.model.get_limits_from_data()
        elif option == DrawCurve.ON_DOMAIN:
            x_min, x_max = self.model.get_fit_domain()
        elif option == DrawCurve.ON_AXIS:
            [[x_min, x_max], _] = self.ui.plot_widget.viewRange()
        return x_min, x_max

    def format_plot_info(self):
        """Format basic plot information in the results box.

        Returns:
            A string containing the formatted plot information.
        """
        msg = make_header("Data sources")
        msg += make_table(
            [
                # make sure everything is a string, even None
                (
                    "X: ",
                    str(self.model.get_x_col_name()),
                    " +- ",
                    str(self.model.get_x_err_col_name() or 0),
                    f" (from {self.data_sheet.name})",
                ),
                (
                    "Y: ",
                    str(self.model.get_y_col_name()),
                    " +- ",
                    str(self.model.get_y_err_col_name() or 0),
                    f" (from {self.data_sheet.name})",
                ),
            ]
        )
        return msg

    def format_fit_results(self):
        """Format the results of the fit in the user interface.

        Returns:
            A string containing the formatted fit results.
        """
        fit = self.model.best_fit
        msg = make_header("Fit statistics")
        msg += make_table(
            [
                ("function evaluations", " = ", f"{fit.nfev:<9.4g}"),
                ("reduced chisquare", " = ", f"{fit.redchi:<9.4g}"),
                ("degrees of freedom", " = ", f"{fit.nfree:<9.4g}"),
            ]
        )

        msg += "\n\n"
        msg += make_header("Fit parameters")
        msg += make_param_table(fit.params)

        return msg

    def export_graph(self, filename, dpi=300):
        """Export graph to a file.

        Args:
            filename: path to the file.
        """
        # x_err, y_err will be 0.0 if no errors are specified
        x, y, x_err, y_err = self.model.get_data()
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()

        plt.figure()
        plt.errorbar(
            x,
            y,
            xerr=x_err,
            yerr=y_err,
            fmt="ko",
            ms=3,
            elinewidth=0.5,
        )

        x_min, x_max = self.get_fit_curve_x_limits()
        x = np.linspace(x_min, x_max, NUM_POINTS)
        y = self.model.evaluate_best_fit(x)
        if y is not None:
            plt.plot(x, y, "b-")

        if self.ui.show_initial_fit.isChecked():
            y = self.model.evaluate_model(x)
            if y is not None:
                plt.plot(x, y, "b-", alpha=0.2)

        if self.model.get_fit_domain_enabled():
            plt.axvspan(*self.model.get_fit_domain(), facecolor="k", alpha=0.1)

        plt.xlabel(self.model.x_label)
        plt.ylabel(self.model.y_label)
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.savefig(filename, dpi=dpi)


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
    if params:
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
    else:
        return ""
