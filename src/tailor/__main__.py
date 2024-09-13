import importlib
import importlib.resources

from PySide6 import QtCore, QtGui, QtWidgets

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


class PreflightApplication(QtWidgets.QApplication):
    """Minimal application showing a splash screen.

    This class imports modules listed in PREFLIGHT_MODULES. These include
    modules that are quite large and take some time to load, especially after a
    cold start when the OS preforms extra malware checks. While loading, a
    splash screen is shown to the user to indicate activity.

    The application can also receive FileOpen events from macOS. If so, the
    filename will be stored and can later be passed on to the main application.

    """

    file_to_open = None

    def __init__(self) -> None:
        super().__init__()

        pixmap = QtGui.QPixmap(
            importlib.resources.files("tailor.resources") / "splashscreen.png"
        )
        splash = QtWidgets.QSplashScreen(pixmap)
        splash.show()
        for num, module in enumerate(PREFLIGHT_MODULES, start=1):
            splash.showMessage(
                f"Importing module {module}... {num}/{len(PREFLIGHT_MODULES)}"
            )
            self.processEvents()
            importlib.import_module(module)
        splash.close()

    def event(self, event):
        """Handle system events."""
        if event.type() == QtCore.QEvent.FileOpen:
            # file open event from macOS, store filename for later retrieval
            self.file_to_open = event.file()
            return True
        return super().event(event)


def preflight():
    """Perform preflight.

    Returns:
        str | None: filename if macOS requested to open a file.
    """
    app = PreflightApplication()
    app.shutdown()
    return app.file_to_open


if __name__ == "__main__":
    if file_to_open := preflight():
        # macOS requested to open a file
        import sys

        # append filename to command-line arguments
        sys.argv.append(file_to_open)

    from tailor.app import main

    # run the main application
    main()
