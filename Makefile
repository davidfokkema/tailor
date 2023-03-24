uisrcdir=src/tailor/resources
uidir=src/tailor

uifiles = ui_tailor.py ui_data_sheet.py ui_create_plot_dialog.py ui_csv_format_dialog.py ui_plot_tab.py

.PHONY: help
help:
	@echo "Run:"
	@echo "make ui     -- translate the UI files to Python files."
	@echo "make build  -- build an installer package."

.PHONY: ui
ui: $(addprefix $(uidir)/,$(uifiles))

$(uidir)/ui_%.py: $(uisrcdir)/%.ui
	pyside6-uic $< -o $@

.PHONY: build
build:
	python -m pip install briefcase==0.3.12
	briefcase create
	python -m pip install tomli
	python pruner.py
	briefcase build
	briefcase package