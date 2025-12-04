"""
API Key input dialog for adding provider API keys.
"""

from PySide2.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                                QDialogButtonBox, QTextEdit)
from PySide2.QtGui import QFont
from PySide2.QtCore import Qt


class ApiKeyDialog(QDialog):
    """Dialog for adding an API key for a provider."""

    def __init__(self, provider_name, display_name, parent=None):
        """
        Initialize the API key input dialog.

        Args:
            provider_name: Internal provider name (e.g., "openai", "fireworks")
            display_name: Display name for the provider (e.g., "OpenAI", "Fireworks")
            parent: Parent widget
        """
        super().__init__(parent)
        self.provider_name = provider_name
        self.display_name = display_name
        self.api_key = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"Add API Key - {self.display_name}")
        self.setMinimumSize(500, 250)

        layout = QVBoxLayout(self)

        # Add title label
        title_label = QLabel(f"Add API Key for {self.display_name}")
        title_label.setFont(QFont("Consolas", 11, QFont.Bold))
        layout.addWidget(title_label)

        # Add info label
        info_label = QLabel(
            f"Enter your {self.display_name} API key below.\n"
            f"The key will be securely stored in your system keyring."
        )
        info_label.setFont(QFont("Consolas", 9))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Add API key input field
        key_label = QLabel("API Key:")
        key_label.setFont(QFont("Consolas", 10))
        layout.addWidget(key_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setFont(QFont("Consolas", 9))
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText(f"Enter your {self.display_name} API key here...")
        layout.addWidget(self.api_key_input)

        # Add helpful links based on provider
        links_text = self._get_provider_links()
        if links_text:
            links_label = QLabel(links_text)
            links_label.setFont(QFont("Consolas", 9))
            links_label.setOpenExternalLinks(True)
            links_label.setWordWrap(True)
            layout.addWidget(links_label)

        layout.addStretch()

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _get_provider_links(self):
        """Get helpful links for obtaining API keys based on provider."""
        links = {
            "openai": '<a href="https://platform.openai.com/api-keys">Get an OpenAI API key</a>',
            "fireworks": '<a href="https://fireworks.ai/account/api-keys">Get a Fireworks API key</a>',
            "anthropic": '<a href="https://console.anthropic.com/settings/keys">Get an Anthropic API key</a>',
        }
        link = links.get(self.provider_name.lower())
        if link:
            return f"Don't have an API key? {link}"
        return ""

    def on_ok_clicked(self):
        """Handle OK button click."""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            # Show error if empty
            from PySide2.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid API key.")
            return

        self.api_key = api_key
        self.accept()

    def get_api_key(self):
        """Return the entered API key."""
        return self.api_key
