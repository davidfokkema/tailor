import importlib
import toga
from toga.style import Pack, pack


PREFLIGHT_MODULES = [
    "pydantic",
    "numpy",
    "scipy.optimize",
    "scipy.stats",
    "matplotlib.pyplot",
    "pandas",
    "lmfit",
    "libcst",
    "PySide6",
    "pyqtgraph",
]


class PreflightImports(toga.app.BackgroundTask):

    def __call__(self, app, **kwargs):
        app.progress.max = len(PREFLIGHT_MODULES)
        for idx, module in enumerate(PREFLIGHT_MODULES):
            app.progress.value = idx
            app.status_label.text = f"Importing {module}..."
            # update interface, yield a delay value?
            yield 0.001
            # import module
            importlib.import_module(module)
        app.loop.stop()


class PreflightWindow(toga.App):
    def startup(self) -> None:
        main_box = toga.Box(style=Pack(direction=pack.COLUMN))
        self.status_label = toga.Label("Importing ...")
        self.progress = toga.ProgressBar()
        main_box.add(self.status_label)
        main_box.add(self.progress)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box

        # threading.Thread(target=self.preflight_imports).start()

        self.main_window.show()
        self.add_background_task(PreflightImports())


if __name__ == "__main__":
    PreflightWindow().main_loop()
    print("done")

    from tailor.app import main

    main()
