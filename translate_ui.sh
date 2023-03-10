UIDIR=src/tailor/resources
OUTDIR=src/tailor

pyside6-uic $UIDIR/tailor.ui -o $OUTDIR/tailor_ui.py
pyside6-uic $UIDIR/create_plot_dialog.ui -o $OUTDIR/create_plot_dialog_ui.py
pyside6-uic $UIDIR/csv_format_dialog.ui -o $OUTDIR/csv_format_dialog_ui.py
pyside6-uic $UIDIR/plot_tab.ui -o $OUTDIR/plot_tab_ui.py