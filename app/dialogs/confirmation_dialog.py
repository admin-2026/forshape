"""
Reusable confirmation dialog for user confirmations.
"""

from PySide2.QtWidgets import QMessageBox


def show_confirmation_dialog(parent, title, message, default_no=True):
    """
    Show a confirmation dialog with Yes/No buttons.

    Args:
        parent: Parent window for the dialog
        title: Dialog window title
        message: Message to display in the dialog
        default_no: If True, No button is default; if False, Yes button is default

    Returns:
        bool: True if user clicked Yes, False if user clicked No
    """
    default_button = QMessageBox.No if default_no else QMessageBox.Yes

    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.Yes | QMessageBox.No,
        default_button,
    )

    return reply == QMessageBox.Yes
