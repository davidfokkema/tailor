import pytest

from tailor.cst_names import get_variable_names, rename_variables


@pytest.mark.parametrize(
    "expression, mapping, expected",
    [
        ("a * x + b", {"x": "col1"}, "a * col1 + b"),
        ("a * sin(x) ** 2", {"x": "col2", "y": "z"}, "a * sin(col2) ** 2"),
        ("a(b(c(d(e)))) + 4", {"c": "X"}, "a(b(X(d(e)))) + 4"),
    ],
)
def test_renaming_variables(expression, mapping, expected):
    assert rename_variables(expression, mapping) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("a * x + b", set(["a", "x", "b"])),
        ("a * sin(x) ** 2", set(["a", "sin", "x"])),
        ("a(b(c(d(e)))) + 4", set(["a", "b", "c", "d", "e"])),
    ],
)
def test_get_variables_name(expression, expected):
    assert get_variable_names(expression) == expected
