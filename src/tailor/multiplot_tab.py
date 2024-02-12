import itertools
from typing import TYPE_CHECKING

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

    def __init__(self, parent: "Application", name: str) -> None:
        super().__init__()
        self.ui = Ui_MultiPlotTab()
        self.ui.setupUi(self)

        self.name = name
        self.parent = parent
        self.model = MultiPlotModel()
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
        self.ui.groupBox.setFixedWidth(400)
        self.ui.plot_selection_layout = QtWidgets.QVBoxLayout()
        self.ui.plot_selection_layout.setContentsMargins(4, 0, 0, 0)
        self.ui.plot_selection_layout.setSpacing(0)
        # add stretch to prevent excessive widget sizes for small numbers of
        # parameters
        self.ui.plot_selection_layout.addStretch()
        self.ui.plot_selection.setLayout(self.ui.plot_selection_layout)

    def refresh_ui(self):
        self.update_plots_ui()
        self.rebuild_plot_selection_ui()

    def update_plots_ui(self) -> None:
        """Add and/or remove parameters if necessary."""
        old_plots = set(self._plots.keys())
        current_plots = set(self.parent.get_plots())
        self.add_plots_to_ui(current_plots - old_plots)
        self.remove_plots_from_ui(old_plots - current_plots)

    def add_plots_to_ui(self, plots: list[PlotTab]) -> None:
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

    def remove_plots_from_ui(self, plots: list[PlotTab]) -> None:
        for plot in plots:
            widget = self._plots.pop(plot)
            self.ui.plot_selection_layout.removeWidget(widget)
            widget.deleteLater()

    def rebuild_plot_selection_ui(self) -> None:
        for idx, plot in enumerate(self.parent.get_plots()):
            self.ui.plot_selection_layout.insertWidget(idx, self._plots[plot])
