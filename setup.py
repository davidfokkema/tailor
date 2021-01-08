from setuptools import setup, find_packages

setup(
    name="analyser",
    version="0.1",
    packages=find_packages(),
    package_data={"analyser": ["analyser.ui", "create_plot_dialog.ui", "plot_tab.ui"]},
    entry_points={"console_scripts": ["analyser = analyser.main_app:main"]},
)
