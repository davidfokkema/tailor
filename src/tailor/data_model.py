"""Data model for the tailor app.

Implements a model to contain the data values as a backend for the
table view used in the app. This class provides an API specific to Tailor.
"""

import numpy as np
import pandas as pd

# treat Inf and -Inf as missing values (e.g. when calling dropna())
pd.options.mode.use_inf_as_na = True


class DataModel:
    """Data model for the tailor app.

    Implements a model to contain the data values as a backend for the
    table view used in the app. This class provides an API specific to Tailor.
    """

    _new_col_num = 0
    _data = None
    _calculated_column_expression = None
    _is_calculated_column_valid = None

    def __init__(self) -> None:
        self._data = pd.DataFrame()
        self._calculated_column_expression = {}
        self._is_calculated_column_valid = {}

    def num_rows(self):
        """Return the number of rows in the table."""
        return len(self._data)

    def num_columns(self):
        """Return the number of columns in the table."""
        return len(self._data.columns)

    def get_value(self, row: int, column: int):
        """Get value at row, column in table

        Args:
            row (int): row number
            column (int): column number
        """
        return self._data.iat[row, column]

    def set_value(self, row: int, column: int, value: float):
        """Set value at row, column in table.

        Args:
            row (int): row number
            column (int): column number
            value (float): value to insert
        """
        self._data.iat[row, column] = value

    def insert_rows(self, row: int, count: int):
        """Insert rows into the table.

        Insert `count` rows into the table at position `row`.

        Args:
            row: an integer row number to indicate the place of insertion.
            count: number of rows to insert
        """
        new_data = pd.DataFrame.from_dict(
            {col: count * [np.nan] for col in self._data.columns}
        )
        self._data = pd.concat(
            [self._data.iloc[:row], new_data, self._data.iloc[row:]]
        ).reset_index(drop=True)

    def remove_rows(self, row: int, count: int):
        """Remove rows from the table.

        Removes a row at the specified row number.

        Args:
            row (int): the first row to remove.
            count (int): the number of rows to remove.
        """
        self._data = self._data.drop(index=range(row, row + count)).reset_index(
            drop=True
        )

    def insert_columns(self, column: int, count: int):
        """Insert columns into the table.

        Insert columns *before* the specified column number.

        Args:
            column (int): a column number to indicate the place of insertion.
            count (int): the number of columns to insert.
        """
        labels = [self._create_new_column_label() for _ in range(count)]
        for idx, label in zip(range(column, column + count), labels):
            self._data.insert(idx, label, np.nan)

    def remove_columns(self, column: int, count: int):
        """Remove columns from the table.

        Removes a column at the specified column number.

        Args:
            column (int): a column number to indicate the place of removal.
            count (int): the number of columns to remove.
        """
        labels = self._data.columns[column : column + count]
        self._data.drop(columns=labels, inplace=True)
        # try:
        #     del self._calculated_column_expression[column_name]
        # except KeyError:
        #     # not a calculated column
        #     pass
        # self.recalculate_all_columns()

    def is_empty(self):
        """Check whether all cells are empty."""
        # check for *all* nans in a row or column
        return self._data.dropna(how="all").empty

    def insert_calculated_column(self, column):
        """Insert a calculated column.

        Insert a column *before* the specified column number. Returns True if
        the insertion was succesful.

        Args:
            column: an integer column number to indicate the place of insertion.

        Returns:
            True if the insertion was succesful, False otherwise.
        """
        column_name = self._create_new_column_name()

        if self.insertColumn(column, column_name=column_name) is True:
            self._calculated_column_expression[column_name] = None
            return True
        else:
            return False

    def rename_column(self, col_idx, new_name):
        """Rename a column.

        Renames the column at the specified index.

        Args:
            col_idx: an integer column number.
            new_name: a string with the new column name.
        """
        old_name = self._data.columns[col_idx]
        new_name = self.normalize_column_name(new_name)
        self._data.rename(columns={old_name: new_name}, inplace=True)
        if self.is_calculated_column(col_name=old_name):
            for d in (
                self._calculated_column_expression,
                self._is_calculated_column_valid,
            ):
                d[new_name] = d.pop(old_name, False)
        self.headerDataChanged.emit(QtCore.Qt.Horizontal, col_idx, col_idx)
        self.show_status("Renamed column.")
        return new_name

    def normalize_column_name(self, name):
        """Normalize column name.

        Change whitespace to underscores and add an underscore if the name
        starts with a number.

        Args:
            name (str): the name to normalize.

        Returns:
            str: the normalized name.
        """
        return re.sub(r"\W+|^(?=\d)", "_", name)

    def update_column_expression(self, col_idx, expression):
        """Update a calculated column with a new expression.

        Args:
            col_idx: an integer column number.
            expression: a string with a mathematical expression used to
                calculate the column values.
        """
        col_name = self.get_column_name(col_idx)
        if self.is_calculated_column(col_idx):
            self._calculated_column_expression[col_name] = expression
            if self.recalculate_column(col_name, expression):
                # calculation was successful
                self.show_status("Updated column values.")

    def recalculate_column(self, col_name, expression=None):
        """Recalculate column values.

        Calculate column values based on its expression. Each column can use
        values from columns to the left of itself. Those values can be accessed
        by using the column name as a variable in the expression.

        Args:
            col_name: a string containing the column name.
            expression: an optional string that contains the mathematical
                expression. If None (the default) the expression is taken from the
                column information.

        Returns:
            True if the calculation was successful, False otherwise.
        """
        # UI must be updated to reflect changes in column values
        self.emit_column_changed(col_name)

        if expression is None:
            # expression must be retrieved from column information
            expression = self._calculated_column_expression[col_name]

        # set up interpreter
        objects = self._get_accessible_columns(col_name)
        aeval = asteval.Interpreter(usersyms=objects)
        try:
            # try to evaluate expression and cast output to a float (series)
            output = aeval(expression, show_errors=False, raise_errors=True)
            if isinstance(output, pd.Series) or isinstance(output, np.ndarray):
                output = output.astype("float64")
            else:
                output = float(output)
        except Exception as exc:
            # error in evaluation or output cannot be cast to a float (series)
            self._is_calculated_column_valid[col_name] = False
            self.show_status(f"Error evaluating expression: {exc}")
            return False
        else:
            # evaluation was successful
            self._data[col_name] = output
            self._is_calculated_column_valid[col_name] = True
            self.show_status(f"Recalculated column values.")
            return True

    def _get_accessible_columns(self, col_name):
        """Get accessible column data for use in expressions.

        When calculating column values each column can access the values of the
        columns to its left by using the column name as a variable. This method
        returns the column data for the accessible columns.

        Args:
            col_name (str): the name of the column that wants to access data.

        Returns:
            dict: a dictionary of column_name, data pairs.
        """
        # accessible columns to the left of current column
        idx = self._data.columns.get_loc(col_name)
        accessible_columns = self._data.columns[:idx]
        data = {
            k: self._data[k]
            for k in accessible_columns
            if self.is_calculated_column_valid(col_name=k)
        }
        return data

    def recalculate_all_columns(self):
        """Recalculate all columns.

        If data is entered or changed, the calculated column values must be
        updated. This method will manually recalculate all column values, from left to right.
        """
        column_names = self.get_column_names()
        for col_idx in range(self.columnCount()):
            if self.is_calculated_column(col_idx):
                self.recalculate_column(column_names[col_idx])

    def get_column_name(self, col_idx):
        """Get column name.

        Get column name at the given index.

        Args:
            col_idx: an integer column number.

        Returns:
            The column name as a string.
        """
        return self._data.columns[col_idx]

    def get_column_names(self):
        """Get list of all column names."""
        return list(self._data.columns)

    def get_column_expression(self, col_idx):
        """Get column expression.

        Get the mathematical expression used to calculate values in the column
        at the given index.

        Args:
            col_idx: an integer column number.

        Returns:
            A string containing the mathematical expression or None.
        """
        col_name = self.get_column_name(col_idx)
        try:
            return self._calculated_column_expression[col_name]
        except KeyError:
            return None

    def get_column(self, col_name):
        """Return column values.

        Args:
            col_name: a string containing the column name.

        Returns:
            A pandas.Series containing the column values.
        """
        return self._data[col_name]

    def get_columns(self, col_names):
        """Return values for multiple columns.

        Args:
            col_names: a list of strings containing the column names.

        Returns:
            A list of pandas.Series containing the column values.
        """
        return [self._data[c] for c in col_names]

    def is_calculated_column(self, col_idx=None, col_name=None):
        """Check if column is calculated.

        Supplied with either a column index or a column name (index takes
        precedence), checks whether the column is calculated from a mathematical
        expression.

        Args:
            col_idx: an integer column index (takes precedence over name).
            col_name: a string containing the column name.

        Returns:
            True if the column is calculated, False otherwise.
        """
        if col_idx is not None:
            col_name = self.get_column_name(col_idx)
        return col_name in self._calculated_column_expression

    def is_calculated_column_valid(self, col_idx=None, col_name=None):
        """Check if a calculated column has valid values.

        Supplied with either a column index or a column name (index takes
        precedence), checks whether the column contains the results of a valid
        calculation. When a calculation fails due to an invalid expression the
        values are invalid.

        Args:
            col_idx: an integer column index (takes precedence over name).
            col_name: a string containing the column name.

        Returns:
            True if the column values are valid, False otherwise.
        """
        if col_idx is not None:
            col_name = self.get_column_name(col_idx)
        if not self.is_calculated_column(col_name=col_name):
            # values are not calculated, so are always valid
            return True
        else:
            return self._is_calculated_column_valid.get(col_name, False)

    def _create_new_column_label(self):
        """Create a label for a new column.

        Creates column labels like col1, col2, etc.

        Returns:
            A string containing the new label.
        """
        self._new_col_num += 1
        return f"col{self._new_col_num}"

    def save_state_to_obj(self, save_obj):
        """Save all data and state to save object.

        Args:
            save_obj: a dictionary to store the data and state.
        """
        save_obj.update(
            {
                "data": self._data.to_dict("list"),
                "calculated_columns": self._calculated_column_expression,
                "new_col_num": self._new_col_num,
            }
        )

    def load_state_from_obj(self, save_obj):
        """Load all data and state from save object.

        Args:
            save_obj: a dictionary that contains the saved data and state.
        """
        self.beginResetModel()
        self._data = pd.DataFrame.from_dict(save_obj["data"])
        self._calculated_column_expression = save_obj["calculated_columns"]
        self._new_col_num = save_obj["new_col_num"]
        self.endResetModel()
        self.recalculate_all_columns()

    def write_csv(self, filename):
        """Write all data to CSV file.

        Args:
            filename: a string containing the full filename.
        """
        self._data.to_csv(filename, index=False)

    def read_csv(
        self,
        filename,
        delimiter=None,
        decimal=".",
        thousands=",",
        header=None,
        skiprows=0,
    ):
        """Read data from CSV file.

        Overwrites all existing data by importing a CSV file.

        Args:
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
        """
        self.beginResetModel()

        self._data = self._read_csv_into_dataframe(
            filename, delimiter, decimal, thousands, header, skiprows
        )
        self._calculated_column_expression = {}
        self.endResetModel()

    def read_and_concat_csv(
        self,
        filename,
        delimiter=None,
        decimal=".",
        thousands=",",
        header=None,
        skiprows=0,
    ):
        """Read data from CSV file and concatenate with current data.

        Overwrites all existing columns by importing a CSV file, but keeps other
        columns.

        Args:
            filename: a string containing the path to the CSV file
            delimiter: a string containing the column delimiter
            decimal: a string containing the decimal separator
            thousands: a string containing the thousands separator
            header: an integer with the row number containing the column names,
                or None.
            skiprows: an integer with the number of rows to skip at start of file
        """
        self.beginResetModel()

        import_data = self._read_csv_into_dataframe(
            filename, delimiter, decimal, thousands, header, skiprows
        )
        # drop imported columns from existing data, ignore missing columns
        old_data = self._data.drop(import_data.columns, axis="columns", errors="ignore")
        # concatenate imported and old data
        new_data = pd.concat([import_data, old_data], axis="columns")
        # drop excess rows, if imported data is shorter than old data
        final_data = new_data.iloc[: len(import_data)]

        # save final data and recalculate values in calculated columns
        self._data = final_data
        self.endResetModel()
        self.recalculate_all_columns()

    def _read_csv_into_dataframe(
        self, filename, delimiter, decimal, thousands, header, skiprows
    ):
        """Read CSV data into pandas DataFrame and normalize columns."""
        df = pd.read_csv(
            filename,
            delimiter=delimiter,
            decimal=decimal,
            thousands=thousands,
            header=header,
            skiprows=skiprows,
        )
        # make sure column names are strings, even for numbered columns
        df.columns = df.columns.astype(str)
        # normalize column names to valid python variable names
        df.columns = df.columns.map(self.normalize_column_name)
        return df
