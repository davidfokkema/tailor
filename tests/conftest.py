"""Pytest configuration for Tailor tests.

This module sets up the testing environment for Qt-based tests,
ensuring that Qt can run in headless environments (CI/CD).
"""

import os
import sys

# Set Qt to use offscreen platform for headless testing
# This must be set before any Qt imports
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6 import QtWidgets


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session.

    This fixture ensures that a QApplication instance exists for all tests
    that require Qt functionality. The application is created once per test
    session and reused across all tests.

    Yields:
        QtWidgets.QApplication: The application instance.
    """
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    yield app
    # Don't quit the app, as it may be reused across tests
