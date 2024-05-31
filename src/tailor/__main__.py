import importlib

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


def preflight_imports():
    for module in PREFLIGHT_MODULES:
        print(f"Importing {module}...")
        importlib.import_module(module)
    print("done.")


if __name__ == "__main__":
    preflight_imports()

    from tailor.app import main

    main()
