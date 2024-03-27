import pathlib

from tailor.app import MainWindow
from tailor.plot_tab import PlotTab

from .test_app import data_sheet, plot_tab, simple_project, simple_project_without_plot


class TestPlotExport:
    def test_export_graph(
        self, simple_project: MainWindow, tmp_path: pathlib.Path
    ) -> None:
        filepath = tmp_path / "plot.png"
        plot: PlotTab = simple_project.ui.tabWidget.widget(2)
        plot.model.set_fit_domain_enabled(True)

        plot.export_graph(filepath)
