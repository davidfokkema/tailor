import importlib
import importlib.resources

from PySide6 import QtGui, QtWidgets

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


def preflight():
    """Perform preflight.

    This function imports modules listed in PREFLIGHT_MODULES. These include
    modules that are quite large and take some time to load, especially after a
    cold start when the OS preforms extra malware checks. While loading, a
    splash screen is shown to the user to indicate activity.
    """
    app = QtWidgets.QApplication()
    pixmap = QtGui.QPixmap(
        importlib.resources.files("tailor.resources") / "splashscreen.png"
    )
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.show()
    for num, module in enumerate(PREFLIGHT_MODULES, start=1):
        splash.showMessage(
            f"Importing module {module}... {num}/{len(PREFLIGHT_MODULES)}"
        )
        app.processEvents()
        importlib.import_module(module)
    splash.close()
    app.shutdown()


if __name__ == "__main__":
    preflight()

    from tailor.app import main

    main()
