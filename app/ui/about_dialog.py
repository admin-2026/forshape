"""
About dialog for ForShape AI GUI.

This module provides the About menu action and dialog showing app version info.
"""

from PySide2.QtWidgets import QAction, QMessageBox

from about import APP_VERSION


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
    QMessageBox.about(parent, "About ForShape AI", f"ForShape AI\nVersion: {APP_VERSION}")
