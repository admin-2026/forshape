"""
About dialog for ForShape AI GUI.

This module provides the About menu action and dialog showing app version info.
"""

import os

from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QAction, QMessageBox

from about import __version__
from shapes import __version__ as SHAPES_API_VERSION

_ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "forshape_icon.svg")


def create_about_menu(main_window):
    """
    Create the Help menu with an About action on the main window's menu bar.

    Args:
        main_window: The QMainWindow to attach the menu to
    """
    help_menu = main_window.menuBar().addMenu("Help")
    about_action = QAction("About", main_window)
    about_action.triggered.connect(lambda: _show_about_dialog(main_window))
    help_menu.addAction(about_action)


def _show_about_dialog(parent):
    """Show the About dialog with version information."""
    msg = QMessageBox(parent)
    msg.setWindowTitle("About ForShape AI")
    msg.setText(f"ForShape AI\nVersion: {__version__}\nShapes API: {SHAPES_API_VERSION}")
    msg.setIconPixmap(QPixmap(_ICON_PATH).scaled(64, 64))
    msg.exec_()
