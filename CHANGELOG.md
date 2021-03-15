# Changelog

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
* When adding columns, the column name is selected and focused so you can immediately type a new column name.
* Added degrees of freedom and relative errors to fit results.
* You now have several options for plotting best-fit curves: on data points, only on the fit domain, or on the full axis.
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