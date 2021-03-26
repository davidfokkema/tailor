# Changelog

## v1.0.0

Ready for deployment in our student labs! (🤞)

### Bugfixes

* When editing a cell, the current value no longer disappears.
* Recalculate column values whenever a data value changes. This did not happen
  if you navigated away from the cell instead of pressing enter.
* Better support saving and loading project files when a column gets renamed and
  the fit object still has the old name.
* When you write 1 * 10 ** 20 instead of 1e20 this is not a float but a very
  large integer. This could result in calculated values being cast to dtype
  'object' which caused problems (e.g. with fits). Now always casts to float64
  after calculations.


### Features

* New custom icon. Handdrawn, so will probably be replaced with something nicer.
* Lots of confirmation dialogs before closing files or tabs.
* You can now rename columns without breaking plots and fits. You still need to
  manually update the model expression, however.
* The results box is now the information box. It also displays the data sources
  which update when columns get renamed.
* Export PNG files with a resolution of 300 DPI (much better!)
* Show much more digits in table cells.
* Now catches exceptions during opening and saving projects with details you can
  copy/paste and send to the developer!
* Lots of small UI tweaks and improvements.


## v0.9.0

### Bugfixes

* Plots update when rows are removed
* Fixed: empty plots when exporting before doing a fit


### Features

* You can now save and open Tailor projects!
* When performing a fit, the initial fit is hidden. When changing parameters it
  is made visible.
* You can now choose part of the data as fit domain. Only data in the domain
  will be fitted, the rest will be ignored. The domain edges is draggable with
  the mouse.
* Fit domain is visible in exported graphs.
* Fit errors are now displayed in the statusbar.
* Statusbar messages now stay visible indefinitely.
* Improved displayed precision in table view (spreadsheet) and fit results.
* When adding columns, the column name is selected and focused so you can
  immediately type a new column name.
* Added degrees of freedom and relative errors to fit results.
* You now have several options for plotting best-fit curves: on data points,
  only on the fit domain, or on the full axis.
* Several UI tweaks.


## v0.8.0

### Features

* Spreadsheet-like editing of data
* Import and export of CSV files
* Add / remove columns or rows
* Add columns based on mathematical expressions
* Create multiple scatter plots with X/Y error bars
* Fit custom models to data based on mathematical expressions
* Models can include a wide range of Python operators and mathematical functions
* Parameters are automatically deduced from the model expression and displayed
  in the user interface
* Start values can be easily changes and an initial fit is updated in the plot
  window
* Bounds on parameters and the ability to fix a parameter to a particular value
* Fit results include reduced chi-square statistic and parameter value and error
  estimations
* Easily adjustable axis labels and ranges
* Zooming and panning of the plot
* Export plot as PNG (bitmap) or PDF (vector) images