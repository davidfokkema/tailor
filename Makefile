uisrcdir=src/tailor/resources
uidir=src/tailor

uifiles = ui_tailor.py ui_data_sheet.py ui_create_plot_dialog.py ui_csv_format_dialog.py ui_plot_tab.py ui_data_source_dialog.py ui_rename_dialog.py ui_preview_dialog.py ui_multiplot_tab.py

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
build-macos:
# 	conda create -n tailor-py311 python=3.11 --yes
	python -m pip install briefcase==0.3.17
	briefcase create
	python pruner.py
	cp build/Info.plist build/tailor/macos/app/Tailor.app/Contents/
	briefcase build
	briefcase package -i "Developer ID Application: David Fokkema (HWB9PKA687)"

build-win:
# 	conda create -n tailor-py311 python=3.11 --yes
	python -m pip install briefcase==0.3.17
	briefcase create
	python pruner.py
	copy build\tailor.wxs build\tailor\windows\app
	copy build\tailor\windows\app\src\app\tailor\resources\document_icon.ico build\tailor\windows\app
	briefcase build
	briefcase package
