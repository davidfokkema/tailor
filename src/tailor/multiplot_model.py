from dataclasses import dataclass

from tailor.plot_tab import PlotTab


@dataclass
class PlotInfo:
    color: str


class MultiPlotModel:
    x_label: str
    y_label: str
    _plots: dict[PlotTab, PlotInfo]

    def __init__(self, x_label: str, y_label: str) -> None:
        self.x_label = x_label
        self.y_label = y_label
        self._plots = {}

    def add_plot(self, plot: PlotTab, color: str) -> None:
        self._plots[plot] = PlotInfo(color=color)

    def remove_plot(self, plot: PlotTab) -> None:
        self._plots.pop(plot)

    def get_plot_info(self, plot: PlotTab) -> PlotInfo:
        return self._plots[plot]
