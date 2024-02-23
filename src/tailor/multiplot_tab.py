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
    from tailor.app import Application

NUM_POINTS = 1000


class MultiPlotTab(QtWidgets.QWidget):
    name: str
    id: int
    parent: "Application"
    model: MultiPlotModel
    _plots: dict[PlotTab, QtWidgets.QHBoxLayout]

    def __init__(
        self, parent: "Application", name: str, id: int, x_label: str, y_label: str
    ) -> None:
        super().__init__()
        self.ui = Ui_MultiPlotTab()
        self.ui.setupUi(self)

        self.name = name
        self.id = id
        self.parent = parent
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
        current_plots = set(self.parent.get_plots())
        self.add_plots_to_ui(current_plots - old_plots)
        self.remove_plots_from_ui(old_plots - current_plots)

    def add_plots_to_ui(self, plots: list[PlotTab]) -> None:
        """Add plots to the list of plots.

        Args:
            plots (list[PlotTab]): the plots to be added to the UI.
        """
        for plot, color in zip(plots, self._color):
            is_enabled = QtWidgets.QCheckBox()
            is_enabled.setObjectName("is_enabled")
            plot_name = QtWidgets.QLabel(plot.name)
            plot_name.setObjectName("plot_name")
            plot_label = QtWidgets.QLineEdit(plot.name)
            plot_label.setObjectName("plot_label")
            color_button = ColorButton(color=color)
            color_button.setObjectName("plot_color")
            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(is_enabled)
            hbox.addWidget(plot_name)
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
        for idx, plot in enumerate(self.parent.get_plots()):
            widget = self._plots[plot]
            # force an update on the plot name
            name = widget.findChild(QtWidgets.QWidget, "plot_name")
            name.setText(plot.name)
            # force an update on the checkbox state
            checkbox: QtWidgets.QCheckBox = widget.findChild(
                QtWidgets.QWidget, "is_enabled"
            )
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

    def add_plot(self, plot: PlotTab) -> None:
        label = self._plots[plot].findChild(QtWidgets.QLineEdit, "plot_label").text()
        color = self._plots[plot].findChild(pg.ColorButton, "plot_color").color().name()
        self.model.add_plot(plot, label, color)

    def update_plot_label(self, plot: PlotTab, text: str) -> None:
        plot_info = self.model.get_plot_info(plot)
        plot_info.label = text

    def update_color(self, plot: PlotTab, color_button: pg.ColorButton) -> None:
        plot_info = self.model.get_plot_info(plot)
        plot_info.color = color_button.color().name()
        self.draw_plot()

    def draw_plot(self) -> None:
        """Create a plot in the widget.

        Create a plot from data in the columns specified by the given column
        names.
        """
        self.ui.plot_widget.clear()
        for plot_tab in self._plots.keys():
            if plot_info := self.model.get_plot_info(plot_tab):
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
                error_bars = pg.ErrorBarItem(
                    x=x,
                    y=y,
                    width=2 * xerr,
                    height=2 * yerr,
                    pen=pg.mkPen(color=plot_info.color),
                )
                self.ui.plot_widget.addItem(error_bars)
                if plot_tab.model.best_fit:
                    x_min, x_max = plot_tab.get_fit_curve_x_limits()
                    x = np.linspace(x_min, x_max, NUM_POINTS)
                    y = plot_tab.model.evaluate_best_fit(x)
                    self.ui.plot_widget.plot(
                        x=x,
                        y=y,
                        symbol=None,
                        pen=pg.mkPen(color=plot_info.color, width=4),
                    )
        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        self.ui.plot_widget.setLabel("left", self.model.y_label)
        self.update_limits()

    def export_graph(self, filename, dpi=300):
        """Export graph to a file.

        Args:
            filename: path to the file.
        """
        plt.figure()
        for plot_tab in self.parent.get_plots():
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
                    x_min, x_max = plot_tab.get_fit_curve_x_limits()
                    x = np.linspace(x_min, x_max, NUM_POINTS)
                    y = plot_tab.model.evaluate_best_fit(x)
                    if y is not None:
                        plt.plot(x, y, "-", color=plot_info.color)

        plt.xlabel(self.model.x_label)
        plt.ylabel(self.model.y_label)
        xmin, xmax, ymin, ymax = self.get_adjusted_limits()
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
