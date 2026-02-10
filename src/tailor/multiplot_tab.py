import itertools
from functools import partial
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from pyqtgraph import ColorButton
from PySide6 import QtCore, QtWidgets

from tailor.multiplot_model import MultiPlotModel
from tailor.plot_tab import PlotTab
from tailor.ui_multiplot_tab import Ui_MultiPlotTab

if TYPE_CHECKING:
    from tailor.app import MainWindow

NUM_POINTS = 1000


class MultiPlotTab(QtWidgets.QWidget):
    name: str
    id: int
    main_window: "MainWindow"
    model: MultiPlotModel
    _plots: dict[PlotTab, QtWidgets.QHBoxLayout]

    def __init__(
        self, main_window: "MainWindow", name: str, id: int, x_label: str, y_label: str
    ) -> None:
        super().__init__()
        self.ui = Ui_MultiPlotTab()
        self.ui.setupUi(self)

        self.name = name
        self.id = id
        self.main_window = main_window
        self.model = MultiPlotModel(x_label, y_label)
        self._plots = {}
        self._color = itertools.cycle(
            [
                "black",
                "blue",
                "green",
                "red",
                "orange",
                "purple",
                "gray",
                "darkcyan",
                "pink",
                "olive",
            ]
        )
        self.finish_ui()
        self.refresh_ui()
        self.connect_ui_events()

    def finish_ui(self) -> None:
        """Finish some final UI stuff from code."""
        self.ui.xlabel.setText(self.model.x_label)
        self.ui.ylabel.setText(self.model.y_label)

        self.ui.groupBox.setFixedWidth(400)
        self.ui.plot_selection_layout = QtWidgets.QVBoxLayout()
        self.ui.plot_selection_layout.setContentsMargins(4, 0, 0, 0)
        self.ui.plot_selection_layout.setSpacing(0)
        # add stretch to prevent excessive widget sizes for small numbers of
        # parameters
        self.ui.plot_selection_layout.addStretch()
        self.ui.plot_selection.setLayout(self.ui.plot_selection_layout)

    def connect_ui_events(self) -> None:
        self.ui.xlabel.textChanged.connect(self.update_xlabel)
        self.ui.ylabel.textChanged.connect(self.update_ylabel)
        self.ui.x_min.textChanged.connect(self.update_x_min)
        self.ui.x_max.textChanged.connect(self.update_x_max)
        self.ui.y_min.textChanged.connect(self.update_y_min)
        self.ui.y_max.textChanged.connect(self.update_y_max)
        self.ui.set_limits_button.clicked.connect(self.update_limits)
        self.ui.plot_widget.sigXRangeChanged.connect(self.updated_plot_range)

    def refresh_ui(self):
        """Refresh UI.

        This method is called when this tab is made visible, or when another tab
        is added or removed.
        """
        self.update_axis_settings_from_model()
        self.update_plots_ui()
        self.rebuild_plot_selection_ui()
        self.draw_plot()

    def update_plots_ui(self) -> None:
        """Add and/or remove parameters if necessary."""
        old_plots = set(self._plots.keys())
        current_plots = set(self.main_window.get_plots())
        self.add_plots_to_ui(current_plots - old_plots)
        self.remove_plots_from_ui(old_plots - current_plots)

    def add_plots_to_ui(self, plots: list[PlotTab]) -> None:
        """Add plots to the list of plots.

        Args:
            plots (list[PlotTab]): the plots to be added to the UI.
        """
        for plot, color in zip(plots, self._color):
            is_enabled = QtWidgets.QCheckBox(plot.name)
            is_enabled.setObjectName("is_enabled_checkbox")
            plot_label = QtWidgets.QLineEdit(plot.name)
            plot_label.setObjectName("plot_label")
            color_button = ColorButton(color=color)
            color_button.setObjectName("plot_color")
            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(is_enabled)
            hbox.addStretch()
            hbox.addWidget(plot_label)
            hbox.addWidget(color_button)
            layout_widget = QtWidgets.QWidget()
            layout_widget.setContentsMargins(0, 0, 0, 0)
            layout_widget.setLayout(hbox)
            self._plots[plot] = layout_widget
            is_enabled.stateChanged.connect(
                partial(self.update_checkbox, plot, is_enabled)
            )
            plot_label.textEdited.connect(partial(self.update_plot_label, plot))
            color_button.sigColorChanging.connect(partial(self.update_color, plot))

    def remove_plots_from_ui(self, plots: list[PlotTab]) -> None:
        """Remove plots from the list of plots.

        Args:
            plots (list[PlotTab]): the plots to be removed from the UI.
        """
        for plot in plots:
            self.model.remove_plot(plot)
            widget = self._plots.pop(plot)
            # FIXME: removeWidget does nothing?!
            # self.ui.plot_selection_layout.removeWidget(widget)
            widget.deleteLater()

    def rebuild_plot_selection_ui(self) -> None:
        """Build up list of plots.

        This will (re)insert all plot names in the plots list in the UI in the
        correct order and will update the checkbox and color from the underlying
        model. Note that the widgets are not being created, that must be handled
        by the `update_plots_ui()` method.
        """
        for idx, plot in enumerate(self.main_window.get_plots()):
            widget = self._plots[plot]
            # force an update on the plot name
            checkbox = widget.findChild(QtWidgets.QCheckBox, "is_enabled_checkbox")
            checkbox.setText(plot.name)
            # force an update on the checkbox state
            checkbox.blockSignals(True)
            if plot_info := self.model.get_plot_info(plot):
                checkbox.setChecked(True)
                # force an update on the plot color
                color_button: pg.ColorButton = widget.findChild(
                    QtWidgets.QWidget, "plot_color"
                )
                color_button.blockSignals(True)
                color_button.setColor(plot_info.color)
                color_button.blockSignals(False)
                # force an update on the plot label
                label: QtWidgets.QLineEdit = widget.findChild(
                    QtWidgets.QLineEdit, "plot_label"
                )
                label.setText(plot_info.label)
            else:
                checkbox.setChecked(False)
            checkbox.blockSignals(False)
            self.ui.plot_selection_layout.insertWidget(idx, self._plots[plot])

    def update_checkbox(
        self, plot: PlotTab, widget: QtWidgets.QCheckBox, state: QtCore.Qt.CheckState
    ) -> None:
        if widget.isChecked():
            self.add_plot(plot)
        else:
            self.model.remove_plot(plot)
        self.draw_plot()
        self.main_window.mark_project_dirty()

    def add_plot(self, plot: PlotTab) -> None:
        label = self._plots[plot].findChild(QtWidgets.QLineEdit, "plot_label").text()
        color = self._plots[plot].findChild(pg.ColorButton, "plot_color").color().name()
        self.model.add_plot(plot, label, color)

    def update_plot_label(self, plot: PlotTab, text: str) -> None:
        plot_info = self.model.get_plot_info(plot)
        plot_info.label = text
        self.main_window.mark_project_dirty()

    def update_color(self, plot: PlotTab, color_button: pg.ColorButton) -> None:
        plot_info = self.model.get_plot_info(plot)
        plot_info.color = color_button.color().name()
        self.draw_plot()
        self.main_window.mark_project_dirty()

    def _draw_plot_items(self) -> None:
        """Draw data points, error bars, and model fits on the plot.

        This method handles the actual drawing of all plot elements.
        It should be called when the plot needs to be redrawn (e.g., on zoom).
        """
        self.ui.plot_widget.clear()
        
        # Get the current axis range for model fit drawing
        [[x_range_min, x_range_max], _] = self.ui.plot_widget.viewRange()
        
        for plot_tab in self._plots.keys():
            if plot_info := self.model.get_plot_info(plot_tab):
                # Draw data points
                x, y, xerr, yerr = plot_tab.model.get_data()
                self.ui.plot_widget.plot(
                    x=x,
                    y=y,
                    symbol="o",
                    pen=None,
                    symbolSize=5,
                    symbolPen=plot_info.color,
                    symbolBrush=plot_info.color,
                )
                
                # Draw error bars
                error_bars = pg.ErrorBarItem(
                    x=x,
                    y=y,
                    width=2 * xerr,
                    height=2 * yerr,
                    pen=pg.mkPen(color=plot_info.color),
                )
                self.ui.plot_widget.addItem(error_bars)
                
                # Draw model fit if available
                if plot_tab.model.best_fit:
                    # Use multiplot's axis range for fit curve limits
                    x_min, x_max = plot_tab.get_fit_curve_x_limits_for_range(
                        x_range_min, x_range_max
                    )
                    x = np.linspace(x_min, x_max, NUM_POINTS)
                    y = plot_tab.model.evaluate_best_fit(x)
                    self.ui.plot_widget.plot(
                        x=x,
                        y=y,
                        symbol=None,
                        pen=pg.mkPen(color=plot_info.color, width=4),
                    )

    def draw_plot(self) -> None:
        """Create a plot in the widget.

        Create a plot from data in the columns specified by the given column
        names. This method draws the plot items, sets axis labels, and updates
        axis limits.
        """
        self._draw_plot_items()
        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        self.ui.plot_widget.setLabel("left", self.model.y_label)
        self.update_limits()

    def updated_plot_range(self) -> None:
        """Handle updated plot range (zoom events).

        When the plot is zoomed, redraw model fit curves for any plots that
        have the 'ON_AXIS' draw curve option enabled. This ensures fit curves
        are redrawn with the correct limits for the multiplot's current view.
        """
        from tailor.plot_tab import DrawCurve
        
        # Check if any included plot has DrawCurve.ON_AXIS selected
        needs_redraw = False
        for plot_tab in self._plots.keys():
            if self.model.get_plot_info(plot_tab):
                if plot_tab.get_draw_curve_option() == DrawCurve.ON_AXIS:
                    needs_redraw = True
                    break
        
        # Only redraw if necessary
        if needs_redraw:
            self._draw_plot_items()

    def export_graph(self, filename, dpi=300):
        """Export graph to a file.

        Args:
            filename: path to the file.
        """
        plt.figure()
        
        # Get the multiplot's axis limits for exporting
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()
        
        for plot_tab in self.main_window.get_plots():
            if self.model.uses_plot(plot_tab):
                plot_info = self.model.get_plot_info(plot_tab)
                x, y, xerr, yerr = plot_tab.model.get_data()
                plt.errorbar(
                    x,
                    y,
                    xerr=xerr,
                    yerr=yerr,
                    fmt="o",
                    ms=3,
                    elinewidth=0.5,
                    color=plot_info.color,
                    label=plot_info.label,
                )

                if plot_tab.model.best_fit:
                    # Use multiplot's axis limits when determining fit curve range
                    x_min, x_max = plot_tab.get_fit_curve_x_limits_for_range(
                        xmin, xmax
                    )
                    x = np.linspace(x_min, x_max, NUM_POINTS)
                    y = plot_tab.model.evaluate_best_fit(x)
                    if y is not None:
                        plt.plot(x, y, "-", color=plot_info.color)

        plt.xlabel(self.model.x_label)
        plt.ylabel(self.model.y_label)
        plt.xlim(xmin, xmax)
        plt.ylim(ymin, ymax)
        plt.legend()
        plt.savefig(filename, dpi=dpi)

    def update_axis_settings_from_model(self) -> None:
        """Update axis labels from model."""
        self.ui.xlabel.setText(self.model.x_label)
        self.ui.ylabel.setText(self.model.y_label)
        self.ui.x_min.setText("" if self.model.x_min is None else str(self.model.x_min))
        self.ui.x_max.setText("" if self.model.x_max is None else str(self.model.x_max))
        self.ui.y_min.setText("" if self.model.y_min is None else str(self.model.y_min))
        self.ui.y_max.setText("" if self.model.y_max is None else str(self.model.y_max))

    def update_xlabel(self):
        """Update the x-axis label of the plot."""
        self.model.x_label = self.ui.xlabel.text()
        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        self.main_window.mark_project_dirty()

    def update_ylabel(self):
        """Update the y-axis label of the plot."""
        self.model.y_label = self.ui.ylabel.text()
        self.ui.plot_widget.setLabel("left", self.model.y_label)
        self.main_window.mark_project_dirty()

    def update_x_min(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.x_min.text())
        except ValueError:
            value = None
        self.model.x_min = value
        self.update_limits()
        self.main_window.mark_project_dirty()

    def update_x_max(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.x_max.text())
        except ValueError:
            value = None
        self.model.x_max = value
        self.update_limits()
        self.main_window.mark_project_dirty()

    def update_y_min(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.y_min.text())
        except ValueError:
            value = None
        self.model.y_min = value
        self.update_limits()
        self.main_window.mark_project_dirty()

    def update_y_max(self):
        """Update the minimum x axis limit."""
        try:
            value = float(self.ui.y_max.text())
        except ValueError:
            value = None
        self.model.y_max = value
        self.update_limits()
        self.main_window.mark_project_dirty()

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
