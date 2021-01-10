from PyQt5 import uic, QtWidgets
import pyqtgraph as pg
import pkg_resources


class VariableError(RuntimeError):
    pass


class PlotTab(QtWidgets.QWidget):
    def __init__(self, data_model):
        super().__init__()

        self.data_model = data_model
        uic.loadUi(pkg_resources.resource_stream("analyser", "plot_tab.ui"), self)
        self.model_func.textEdited.connect(lambda: self.update_fit_params())

    def create_plot(self, x_var, y_var, x_err, y_err):
        x, y = self.data_model.get_columns([x_var, y_var])
        if x_err:
            width = 2 * self.data_model.get_column(x_err)
        else:
            width = None
        if y_err:
            height = 2 * self.data_model.get_column(y_err)
        else:
            height = None
        self.plot_widget.plot(
            x, y, symbol="o", pen=None, symbolSize=5, symbolPen="k", symbolBrush="k",
        )
        error_bars = pg.ErrorBarItem(x=x, y=y, width=width, height=height)
        self.plot_widget.addItem(error_bars)
        self.plot_widget.setLabel("left", y_var)
        self.plot_widget.setLabel("bottom", x_var)
        self.update_function_label(y_var)
        self._y_var = y_var
        self._x_var = x_var

    def update_function_label(self, variable):
        label_text = self.model_func_label.text()
        title, _, _ = label_text.partition(":")
        new_label_text = f"{title}:  {variable} ="
        self.model_func_label.setText(new_label_text)

    def update_fit_params(self):
        try:
            params = self.get_params_from_model()
        except (SyntaxError, VariableError) as exc:
            print(exc)
            return
        else:
            self.result_box.setPlainText(", ".join(params))

    def get_params_from_model(self):
        code = compile(self.model_func.text(), "<string>", "eval")
        params = set(code.co_names) - set(self._x_var)
        if self._y_var in params:
            raise VariableError(
                f"Dependent variable {self._y_var} must not be in function definition"
            )
        else:
            return params
