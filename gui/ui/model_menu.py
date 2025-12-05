"""
Model and provider menu management for ForShape AI GUI.

This module provides functionality for managing the model selection menu,
including provider selection, model dropdowns, and API key management.
"""

from PySide2.QtWidgets import QLabel, QComboBox, QWidget, QHBoxLayout, QWidgetAction, QAction, QDialog
from PySide2.QtGui import QFont


class ModelMenuManager:
    """Handles model and provider menu creation and management."""

    def __init__(self, provider_config_loader, message_handler, logger=None):
        """
        Initialize the model menu manager.

        Args:
            provider_config_loader: ProviderConfigLoader instance
            message_handler: MessageHandler instance for displaying messages
            logger: Optional Logger instance
        """
        self.provider_config_loader = provider_config_loader
        self.message_handler = message_handler
        self.logger = logger

        # Dictionary to store model combo boxes for each provider
        self.model_combos = {}

        # These will be set by main window
        self.ai_client = None
        self.prestart_checker = None
        self.completion_callback = None
        self.enable_ai_mode_callback = None

    def set_ai_client(self, ai_client):
        """Set the AI client reference."""
        self.ai_client = ai_client

    def set_callbacks(self, prestart_checker, completion_callback, enable_ai_mode_callback):
        """Set callbacks for prestart checks and completion."""
        self.prestart_checker = prestart_checker
        self.completion_callback = completion_callback
        self.enable_ai_mode_callback = enable_ai_mode_callback

    def create_model_menu_items(self, model_menu, parent_window):
        """
        Dynamically create model menu items from provider configuration.
        If a provider is missing an API key, show an "Add API Key" button instead of a dropdown.

        Args:
            model_menu: The QMenu to add model selection widgets to
            parent_window: Parent window for dialogs
        """
        from ..api_key_manager import ApiKeyManager

        providers = self.provider_config_loader.get_providers()

        if not providers:
            # No providers configured, show a message
            no_providers_label = QLabel("  No providers configured")
            no_providers_label.setFont(QFont("Consolas", 9))
            model_menu.addAction(QWidgetAction(parent_window))
            return

        # Check API keys for all providers
        api_key_manager = ApiKeyManager()

        # Create a section for each provider
        for provider in providers:
            # Create label for provider
            provider_label = QLabel(f"  {provider.display_name}: ")
            provider_label.setFont(QFont("Consolas", 9, QFont.Bold))

            # Check if API key exists for this provider
            api_key = api_key_manager.get_api_key(provider.name)

            # Create a widget container for label and combo/button
            provider_widget = QWidget()
            provider_layout = QHBoxLayout(provider_widget)
            provider_layout.setContentsMargins(5, 2, 5, 2)
            provider_layout.addWidget(provider_label)

            if api_key:
                # API key exists - show model dropdown
                model_combo = QComboBox()
                model_combo.setFont(QFont("Consolas", 9))

                # Add placeholder as first option
                model_combo.addItem("-- Select --", None)

                # Add all models for this provider
                default_index = 0
                for idx, model in enumerate(provider.models, start=1):
                    model_combo.addItem(model.display_name, model.name)
                    # Set default if this is the default model
                    if model.name == provider.default_model:
                        default_index = idx

                # Set the default model if configured
                if default_index > 0:
                    model_combo.setCurrentIndex(default_index)

                # Connect change event
                model_combo.currentIndexChanged.connect(
                    lambda idx, prov=provider.name: self.on_model_changed(idx, prov)
                )

                # Store the combo box for later access
                self.model_combos[provider.name] = model_combo

                provider_layout.addWidget(model_combo)
                provider_layout.addStretch()

                # Add the widget to the menu using QWidgetAction
                provider_action = QWidgetAction(parent_window)
                provider_action.setDefaultWidget(provider_widget)
                model_menu.addAction(provider_action)
            else:
                # API key missing - show a clickable menu action instead of a button widget
                # First add the label as a widget
                provider_action = QWidgetAction(parent_window)
                provider_action.setDefaultWidget(provider_widget)
                model_menu.addAction(provider_action)

                # Then add a clickable "Add API Key" action
                add_key_action = QAction(f"      → Add API Key", parent_window)

                # Use a closure-safe connection
                def make_handler(prov, disp, parent):
                    def handler():
                        self.on_add_api_key(prov, disp, parent)
                    return handler

                add_key_action.triggered.connect(make_handler(provider.name, provider.display_name, parent_window))
                model_menu.addAction(add_key_action)

    def on_model_changed(self, index: int, provider: str):
        """
        Handle model dropdown selection change.

        Args:
            index: The index of the selected item in the combo box
            provider: The provider name (e.g., "openai", "fireworks")
        """
        if not self.ai_client:
            return

        # Get the combo box for this provider
        combo_box = self.model_combos.get(provider)
        if not combo_box:
            return

        # Get the model identifier from the combo box data
        model = combo_box.itemData(index)
        model_name = combo_box.itemText(index)

        # If placeholder is selected (model is None), do nothing
        if model is None:
            return

        # Clear all other providers' selections
        for other_provider, other_combo in self.model_combos.items():
            if other_provider != provider:
                try:
                    other_combo.currentIndexChanged.disconnect()
                except:
                    pass
                other_combo.setCurrentIndex(0)  # Reset to placeholder
                # Reconnect the signal
                other_combo.currentIndexChanged.connect(
                    lambda idx, prov=other_provider: self.on_model_changed(idx, prov)
                )

        # Get provider-specific API key from keyring
        from ..api_key_manager import ApiKeyManager
        api_key_manager = ApiKeyManager()
        api_key = api_key_manager.get_api_key(provider)

        # Check if API key exists for this provider
        if not api_key:
            provider_config = self.provider_config_loader.get_provider(provider)
            display_name = provider_config.display_name if provider_config else provider.capitalize()
            self.message_handler.append_message("System", f"No API key configured for {display_name}. Please add the API key to the system keyring using ApiKeyManager.")
            return

        # Get provider config for base_url and other settings
        provider_config = self.provider_config_loader.get_provider(provider)

        # Reinitialize the AI agent with the new provider
        from ..api_provider import create_api_provider_from_config
        if provider_config:
            new_provider = create_api_provider_from_config(provider_config, api_key)
        else:
            # Fallback to basic provider creation if config not found
            from ..api_provider import create_api_provider
            new_provider = create_api_provider(provider, api_key)

        if new_provider and new_provider.is_available():
            self.ai_client.provider = new_provider
            self.ai_client.provider_name = provider
            self.ai_client.set_model(model)

            # Get display name from config
            display_name = provider_config.display_name if provider_config else provider.capitalize()

            # Show a confirmation message
            self.message_handler.append_message("System", f"Provider changed to: {display_name}\nModel changed to: {model_name} ({model})")
        else:
            display_name = provider_config.display_name if provider_config else provider.capitalize()
            self.message_handler.append_message("System", f"Failed to initialize {display_name} provider. Please check your API key configuration.")

    def on_add_api_key(self, provider_name: str, display_name: str, parent_window):
        """
        Handle "Add API Key" action click for a provider.

        Args:
            provider_name: Internal provider name (e.g., "openai", "fireworks")
            display_name: Display name for the provider (e.g., "OpenAI", "Fireworks")
            parent_window: Parent window for the dialog
        """
        try:
            from ..dialogs import ApiKeyDialog

            # Show API key input dialog
            dialog = ApiKeyDialog(provider_name, display_name, parent_window)
            if dialog.exec_() == QDialog.Accepted:
                api_key = dialog.get_api_key()
                if api_key:
                    # Save the API key using ApiKeyManager
                    from ..api_key_manager import ApiKeyManager
                    api_key_manager = ApiKeyManager()
                    api_key_manager.set_api_key(provider_name, api_key)

                    # Show success message
                    self.message_handler.append_message("System", f"API key for {display_name} has been saved successfully!")

                    # Refresh the Model menu to show the dropdown instead of the button
                    self.refresh_model_menu(parent_window)

                    # If this is the first API key and AI client is not initialized yet,
                    # we might need to trigger completion callback
                    if self.completion_callback and not self.ai_client:
                        # Re-run prestart checks which should now pass
                        if self.prestart_checker:
                            status = self.prestart_checker.check(parent_window)
                            if status == "ready":
                                self.completion_callback()
                                if self.enable_ai_mode_callback:
                                    self.enable_ai_mode_callback()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding API key: {e}")
            self.message_handler.append_message("[ERROR]", f"Failed to add API key: {str(e)}")

    def refresh_model_menu(self, parent_window):
        """
        Refresh the Model menu to update API key status and available models.

        Args:
            parent_window: Parent window to get menubar from
        """
        # Find and clear the Model menu
        menubar = parent_window.menuBar()
        for action in menubar.actions():
            if action.text() == "Model":
                menu = action.menu()
                if menu:
                    # Clear all actions
                    menu.clear()
                    # Clear stored combo boxes
                    self.model_combos.clear()
                    # Recreate menu items
                    self.create_model_menu_items(menu, parent_window)
                break

    def sync_model_dropdown(self):
        """Sync the model dropdown selection with the AI client's current model and provider."""
        if not self.ai_client:
            return

        current_model = self.ai_client.get_model()
        current_provider = self.ai_client.provider_name

        # Get the combo box for the current provider
        combo_box = self.model_combos.get(current_provider)
        if not combo_box:
            # Unknown provider, keep current dropdown selection
            return

        # Reset all other providers' dropdowns to placeholder
        for other_provider, other_combo in self.model_combos.items():
            if other_provider != current_provider:
                try:
                    other_combo.currentIndexChanged.disconnect()
                except:
                    pass
                other_combo.setCurrentIndex(0)  # Reset to placeholder
                # Reconnect signal
                other_combo.currentIndexChanged.connect(
                    lambda idx, prov=other_provider: self.on_model_changed(idx, prov)
                )

        # Find and select the matching model in the current provider's dropdown
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == current_model:
                # Temporarily disconnect signal to avoid triggering on_model_changed
                try:
                    combo_box.currentIndexChanged.disconnect()
                except:
                    pass
                combo_box.setCurrentIndex(i)
                # Reconnect signal
                combo_box.currentIndexChanged.connect(
                    lambda idx, prov=current_provider: self.on_model_changed(idx, prov)
                )
                return

        # If model not found in dropdown, it might be a custom model
        # Keep current dropdown selection as is
