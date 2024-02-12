import itertools
from functools import partial
from typing import TYPE_CHECKING

import pyqtgraph as pg
from pyqtgraph import ColorButton
from PySide6 import QtCore, QtWidgets

from tailor.multiplot_model import MultiPlotModel
from tailor.plot_tab import PlotTab
from tailor.ui_multiplot_tab import Ui_MultiPlotTab

if TYPE_CHECKING:
    from tailor.app import Application


class MultiPlotTab(QtWidgets.QWidget):
    name: str
    parent: "Application"
    model: MultiPlotModel
    _plots: dict[PlotTab, QtWidgets.QHBoxLayout]

    def __init__(
        self, parent: "Application", name: str, x_label: str, y_label: str
    ) -> None:
        super().__init__()
        self.ui = Ui_MultiPlotTab()
        self.ui.setupUi(self)

        self.name = name
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

    def refresh_ui(self):
        """Refresh UI.

        This method is called when this tab is made visible, or when another tab
        is added or removed.
        """
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
            plot_name = QtWidgets.QLabel(plot.name)
            is_enabled = QtWidgets.QCheckBox()
            is_enabled.setObjectName("is_enabled")
            color_button = ColorButton(color=color)
            color_button.setObjectName("plot_color")
            hbox = QtWidgets.QHBoxLayout()
            hbox.addWidget(is_enabled)
            hbox.addWidget(plot_name)
            hbox.addStretch()
            hbox.addWidget(color_button)
            layout_widget = QtWidgets.QWidget()
            layout_widget.setContentsMargins(0, 0, 0, 0)
            layout_widget.setLayout(hbox)
            self._plots[plot] = layout_widget
            is_enabled.stateChanged.connect(
                partial(self.update_checkbox, plot, is_enabled)
            )
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

        This will (re)insert all plot names in the plots list in the UI.
        """
        for idx, plot in enumerate(self.parent.get_plots()):
            self.ui.plot_selection_layout.insertWidget(idx, self._plots[plot])

    def update_checkbox(
        self, plot: PlotTab, widget: QtWidgets.QCheckBox, state: QtCore.Qt.CheckState
    ) -> None:
        if widget.isChecked():
            color = widget.parent().findChild(pg.ColorButton, "plot_color").color()
            self.model.add_plot(plot, color)
        else:
            self.model.remove_plot(plot)
        self.draw_plot()

    def update_color(self, plot: PlotTab, color_button: pg.ColorButton) -> None:
        plot_info = self.model.get_plot_info(plot)
        plot_info.color = color_button.color()
        self.draw_plot()

    def draw_plot(self) -> None:
        """Create a plot in the widget.

        Create a plot from data in the columns specified by the given column
        names.
        """
        self.ui.plot_widget.clear()
        for plot_tab in self._plots.keys():
            try:
                plot_info = self.model.get_plot_info(plot_tab)
            except KeyError:
                pass
            else:
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
                error_bars = pg.ErrorBarItem(x=x, y=y, width=2 * xerr, height=2 * yerr)
                self.ui.plot_widget.addItem(error_bars)
                # fit_plot = self.ui.plot_widget.plot(
                #     symbol=None, pen=pg.mkPen(color="#00F", width=4)
                # )
        self.ui.plot_widget.setLabel("bottom", self.model.x_label)
        self.ui.plot_widget.setLabel("left", self.model.y_label)
