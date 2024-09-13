# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Tailor now follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions.

### Fixed

- Open Tailor projects from Finder, don't show an empty window (#84).
- Changing a value in a cell again shows a free-form text editor, instead of a restrictive two-decimal DoubleSpinBox which didn't accept scientific notation like 1.2e-3.
- Correctly handle dark mode on Windows.

## 2.0.4

### :rocket: Features

* Shows a splash screen during import of large Python packages.


## 2.0.3

### :rocket: Features

* Columns are now resizable using the mouse


### :beetle: Fixes

* Improved float representation (better fits into a column, won't break up to "0...")


## 2.0.2

### :beetle: Fixes

* Fixed a bug where closing a plot would close the plot _and_ the next tab widget. This is never desired and could lead to the loss of data if the next widget was a data sheet. If there were plots for that data sheet, the project could never be opened again. Loading the project would raise an exeception because of the missing data sheet being referenced by the surviving plot. Thanks for the detailed report, Jurre Heijmen!


## 2.0.1

### :beetle: Fixes

* Improved data refresh times by 10x so that changing column expressions no longer freezes the interface for large datasets.
* Fixed a bug where it was possible to save a corrupt project when you removed almost all data rows.
* Much faster row removal by removing rows in selection blocks instead of removing individual rows.


## 2.0.0

About eight months have passed since the previous release of Tailor and many (long-requested) features have been added. Work on the 2.0 branch already started in May, 2023 with the refactoring of large parts of the code to make it more modular. This enabled us to separate data sheets, plots and underlying data models which led to simpler, more robust and better testable code. It then became easier to add functionality for creating multiple data sheets, multiplots, etc. and fixing some long-standing bugs. Our guiding principle always was to build the most simple and intuitive interface possible, even while adding features. Enjoy!


### :rocket: Features

* Added 300+ unit and integration tests.
* You can now create more data sheets to analyse multiple experiments.
* You can now duplicate a sheet, either with or without all associated plots, as a basis for analysing new measurements.
* Plot multiple datasets and model fits in a single graph.
* Double-clicking on Tailor files now opens them in the application on MacOS and Windows. (#73)
* Totally re-engineered file format, but legacy projects can still be opened.
* You can now preview an exported graph to quickly see how it will turn out and make changes.
* For MacOS, universal binaries are now available. It is no longer necessary to choose between Intel and Apple silicon.
* Renaming columns effectively updates all references used in calculated columns, plots, fit models, etc.
* Initial fit and best fit now both have a blue color.
* When data, fit models, fit ranges, initial fit parameters or bounds, etc. change the best fit is invalidated indicated by a red color.
* Plot information is reordered to show the most important information at the top.
* Loading and saving project files use Pydantic for validation.
* When removing a column, refuse if it is used in calculated columns or plots, and list where it is used.
* When removing a data sheet, list all plots where it is used and ask for confirmation before deleting the sheet and all associated plots.
* You can now duplicate a plot to try fitting other models.
* You can change the source of a plot to use another data sheet or other data columns for x and y axes and uncertainties.
* When a fit fails you now get some suggestions along with a detailed error message.
* Show a red border to indicate problems with calculated model or fit model expressions.
* When enclosing the model in parentheses, you can use newlines to separate parts of the expression.
* Upgraded to Qt/PySide 6.6 and Pandas 2.0, amongst other updates.


### :beetle: Fixes

* Only indicate there are unsaved changes when the project was actually changed. (#22)
* Cursor no longer jumps to end of line when editing column names. (#79)
* Initial fit curves now respect 'draw curve range' setting. (#75)
* Developer name is removed from install location on Windows. (#71)
* Fixed selection bug where first selecting a column and then selecting a single cell within that column did not update all column information correctly.
* Use scrollbars in the tab widget when there are many tabs.


### :hammer: Refactoring

* Completely overhauled separation of concerns between GUI and data model layers. There are now more layers and many methods are now more focused and well tested. Should also make it easier to switch GUI toolkits in the future.
* Sheets and plots now keep references to columns using static labels. When a tab is focused, the UI updates itself using these references. It is therefore no longer necessary to track renaming of columns, etc.
* Added 300+ unit and integration tests.



## 1.8.0

### :rocket: Features

* Added `--no-update-check` flag to skip updates on startup
* Improved resilience against NaNs when fitting a model

### :beetle: Fixes

* Check for both OS and CPU hardware for updates (e.g. differentiate between Intel and Apple Silicon)
* Include link to release notes in update window
* Much improved dialog for available updates
* Slim down Windows application


## 1.7.0

### What's Changed

We now have fully signed, notarized and native builds for Apple Silicon. Builds for Windows are submitted to Microsoft for analysis so there should never be any warning that Tailor is untrusted, from an unidentified developer, or not commonly downloaded 😀. Unfortunately, universal builds are very difficult because some Python packages don't supply universal wheels and GitHub Actions does not have Apple Silicon machines. So, only Windows builds are done on GitHub Actions and Mac builds are done on two local machines.

### :package: Build system

* Signed, notarized and native builds for Macs on Intel and Apple Silicon


## 1.6.1

### What's Changed

I no longer use release drafter. It is a nice idea but I had to create pull requests for _everything_ or it wouldn't show up in the release notes and I still had to copy/paste these notes to the CHANGELOG.md file. Furthermore, I had to rerun the GitHub Action if I made a typo in the PR title.

### :package: Build system

* Ditched release drafter, too much overkill.
* We can use the newest briefcase on Windows (beeware/briefcase#930)


### :rocket: Features
### :beetle: Fixes

* Accept NumPy arrays as output of functions


## 1.6.0
### What’s Changed

This release includes several enhancements, the most notable being support for copy and paste in the data sheet. It is now easy to copy and paste entire columns, or copy data to and from a spreadsheet application like Numbers or Excel. The plot interface is also a bit improved when a model includes a large number of parameters. Since the list of parameters is now scrollable the size stays relatively small so there's more room for the model function and the information window.

Several bugs are fixed including a fatal unicode decoding bug. Under the hood parts of the code are refactored to reduce complexity and make it easier to further develop the code base.

### :rocket: Features

* Move axis settings and buttons below plot (#66) @davidfokkema
* Improve plot tab user interface layout (#65) @davidfokkema
* Add copy/paste behaviour (#61) @davidfokkema

### :beetle: Fixes

* Insert model parameters in alphabetical order (#64) @davidfokkema
* Fix unicode decoding errors on Windows in TOML config (#59) @davidfokkema

### :hammer: Refactoring

* Improve plot tab user interface layout (#65) @davidfokkema
* Simplified logic and improved error messages for calculated columns (#63) @davidfokkema
* Refactored column ordering (#62) @davidfokkema


## 1.5.3

### :package: Build System

* New version of briefcase; crashes on Windows now show error messages

### :rocket: Features

* New version of PySide6, only the 'Essentials' package

### :beetle: Fixes

* Fix toml decoding error (#56) @davidfokkema


## v1.5.2

### :rocket: Features

* Speed up clearing cells (#54) @davidfokkema
* Ignore line endings in model expression (#49) @davidfokkema

### :beetle: Fixes

* Update plots on import of CSV files (#55) @davidfokkema
* Reset column ordering when opening a new project (#53) @davidfokkema
* Really fix missing columns (#52) @davidfokkema
* Correctly restart dirty flag timer (#51) @davidfokkema
* Recalculate values when removing rows or columns (#50) @davidfokkema
* Handle network issues when checking for updates (#48) @davidfokkema


## v1.5.1

### :beetle: Fixes

* Saving project updates recent files and dirty flag (#44) @davidfokkema
* Set correct column order when importing CSV (fixes missing columns) (#43) @davidfokkema


## v1.5.0

### What’s Changed

Nice update with several usability enhancements and bug fixes.

### :rocket: Features

* Check for new releases (#37) @davidfokkema
* Only confirm closing a project when some time has passed (#36) @davidfokkema
* Calculate column values in a strict order (left to right) (#34) @davidfokkema
* Move columns by dragging the column header (#31) @davidfokkema
* Change model function input to multi-line text field (#28) @davidfokkema
* Added shortcuts for menu items (#27) @davidfokkema
* Remember cwd and recent files (#26) @davidfokkema
* Upgrade and switch from PyQt5 to PySide6 (#21) @davidfokkema

### :beetle: Fixes

* Fix crash when model has no parameters (#35) @davidfokkema
* Fix crashes when moving columns (#33) @davidfokkema
* Do not ignore NaN values in fit (#32) @davidfokkema
* Hide autoscale button in plots (fix infinite zoom) (#30) @davidfokkema
* Normalize column names when editing (#29) @davidfokkema


## v1.4.2

### What’s Changed

Minor update, but fixes a serious bug.

### :rocket: Features

* Normalise column names when importing CSV (#14)

### :beetle: Fixes

* Solves weird behaviour when editing cells caused by resetting the model when calculating values


## v1.4.1

### What’s Changed

This is a minor bugfix update.

### :beetle: Fixes

* Fix: recalculate values when clearing cells


## v1.4.0

### What’s Changed

Some enhancements for easier reuse of projects: import new data into current project and clear contents of selected cells.

### :rocket: Features

* Clear selected cells (#12)
* Import CSV file into project (#11)


## v1.3.0

### What’s Changed

This is a bugfix update with some minor new features.

### :rocket: Features

* You can now use backspace and delete keys to clear cell contents
* Empty cells are now handled gracefully by plots, fits and in open/save projects
* Column labels are now more consistently cleared when changing selections

### :beetle: Fixes

* Fix handling of Inf and NaN values (#8), fixes #5 and #7 
* Exceptions when saving plots fail silently (#6)
* Removing calculated column keeps name in memory (#1)

### :package: Build System

* No longer use fork of dmgbuild


## v1.2.0

### What’s Changed

This is a minor update.

### :rocket: Features

* Added a semicolon to the list of CSV-like column delimiters
* Improved error handling of CSV imports, including more useful help messages

### :package: Build System

* We now use GitHub Actions to build our MacOS and Windows installers


## v1.1.1

### Bugfixes

* When a model function previously was correct but is now broken (e.g. missing
  closing bracket) a fit would be performed with the old model function. This
  hid the error message complaining about the model, which was not ideal... Now,
  trying to perform a fit will really complain about the broken model.


### Features

* There are now several file filters available to import *.txt or other files.
* Exceptions during the opening of Tailor projects are now better handled and reported.


## v1.1.0

### Features

* Import not-quite-CSV-files (tabs, comments, etc.) with a nice preview window.
* Icon size corrected for MacOS.
* Ask for confirmation *before* opening or importing files or projects, not *after* selecting the file.


## v1.0.2

### Bugfixes

* Fixes a crash when calculating the relative error when the parameter value is zero.


## v1.0.1

### Bugfixes

* When entering constants (like 0.8) in a calculated column, the single-valued
  float type could not be cast using the .astype() method triggering an
  exception.
* When changing the draw curve region option (e.g. from 'On data point' to 'On
  full axis') the plot was not updated correctly.


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