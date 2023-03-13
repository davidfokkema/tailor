UIDIR=src/tailor/resources
OUTDIR=src/tailor

pyside6-uic $UIDIR/tailor.ui -o $OUTDIR/ui_tailor.py
pyside6-uic $UIDIR/create_plot_dialog.ui -o $OUTDIR/ui_create_plot_dialog.py
pyside6-uic $UIDIR/csv_format_dialog.ui -o $OUTDIR/ui_csv_format_dialog.py
pyside6-uic $UIDIR/plot_tab.ui -o $OUTDIR/ui_plot_tab.py