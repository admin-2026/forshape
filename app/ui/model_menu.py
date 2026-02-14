"""
Model and provider menu management for ForShape AI GUI.

This module provides functionality for managing the model selection menu,
including provider selection, model dropdowns, and API key management.
"""

from PySide2.QtGui import QFont
from PySide2.QtWidgets import QAction, QComboBox, QDialog, QHBoxLayout, QLabel, QWidget, QWidgetAction


class ModelMenuManager:
    """Handles model and provider menu creation and management."""

    def __init__(self, provider_config_loader, message_handler, logger, ui_config_manager=None):
        """
        Initialize the model menu manager.

        Args:
            provider_config_loader: ProviderConfigLoader instance
            message_handler: ConversationView instance for displaying messages
            logger: Logger instance
            ui_config_manager: Optional UIConfigManager instance for persisting selections
        """
        self.provider_config_loader = provider_config_loader
        self.message_handler = message_handler
        self.logger = logger
        self.ui_config_manager = ui_config_manager

        # Dictionary to store model combo boxes for each provider
        self.model_combos = {}

        # Cached API key manager instance
        self._api_key_manager = None

        # These will be set by main window
        self.ai_client = None
        self.prestart_checker = None
        self.enable_ai_mode_callback = None

    def set_ai_client(self, ai_client):
        """Set the AI client reference."""
        self.ai_client = ai_client

    def set_callbacks(self, prestart_checker, enable_ai_mode_callback):
        """Set callbacks for prestart checks and AI mode enabling."""
        self.prestart_checker = prestart_checker
        self.enable_ai_mode_callback = enable_ai_mode_callback

    def _get_api_key_manager(self):
        """Get or create the API key manager instance."""
        if self._api_key_manager is None:
            from agent.api_key_manager import ApiKeyManager

            self._api_key_manager = ApiKeyManager()
        return self._api_key_manager

    def _get_provider_display_name(self, provider_name):
        """Get the display name for a provider."""
        provider_config = self.provider_config_loader.get_provider(provider_name)
        return provider_config.display_name if provider_config else provider_name.capitalize()

    def _reset_other_provider_dropdowns(self, current_provider):
        """Reset all other providers' dropdowns to placeholder."""
        for other_provider, other_combo in self.model_combos.items():
            if other_provider != current_provider:
                other_combo.blockSignals(True)
                other_combo.setCurrentIndex(0)  # Reset to placeholder
                other_combo.blockSignals(False)

    def _initialize_provider(self, provider_name, api_key):
        """
        Initialize a provider with the given API key.

        Args:
            provider_name: The provider name
            api_key: The API key for the provider

        Returns:
            Initialized provider instance or None if failed
        """
        from agent.api_provider import create_api_provider, create_api_provider_from_config

        provider_config = self.provider_config_loader.get_provider(provider_name)
        if provider_config:
            return create_api_provider_from_config(provider_config, api_key)
        else:
            return create_api_provider(provider_name, api_key)

    def _switch_to_provider_model(self, provider_name, model, model_name=None):
        """
        Switch AI client to use the specified provider and model.

        Args:
            provider_name: The provider name
            model: The model identifier
            model_name: Optional display name for the model

        Returns:
            bool: True if successful, False otherwise
        """
        api_key_manager = self._get_api_key_manager()
        api_key = api_key_manager.get_api_key(provider_name)

        if not api_key:
            display_name = self._get_provider_display_name(provider_name)
            if self.message_handler:
                self.message_handler.append_message("System", f"No API key configured for {display_name}.")
            return False

        new_provider = self._initialize_provider(provider_name, api_key)

        if new_provider and new_provider.is_available():
            self.ai_client.provider = new_provider
            self.ai_client.provider_name = provider_name
            self.ai_client.set_model(model)

            # Save to config
            if self.ui_config_manager:
                self.ui_config_manager.update({"selected_provider": provider_name, "selected_model": model})

            # Refresh welcome widget to reflect new model
            if self.message_handler:
                self.message_handler.welcome_widget.refresh()

            # Show confirmation message
            if self.message_handler and model_name:
                display_name = self._get_provider_display_name(provider_name)
                self.message_handler.append_message(
                    "System", f"Provider changed to: {display_name}\nModel changed to: {model_name} ({model})"
                )

            return True
        else:
            display_name = self._get_provider_display_name(provider_name)
            if self.message_handler:
                self.message_handler.append_message("System", f"Failed to initialize {display_name} provider.")
            return False

    def _select_first_available_provider(self):
        """
        Find and select the first provider with an API key and available models.

        Returns:
            bool: True if a provider was selected, False otherwise
        """
        api_key_manager = self._get_api_key_manager()
        providers = self.provider_config_loader.get_providers()

        for provider in providers:
            api_key = api_key_manager.get_api_key(provider.name)
            if api_key and provider.models:
                # Use the default model or the first model
                model_to_select = provider.default_model or (provider.models[0].name if provider.models else None)

                if model_to_select:
                    combo_box = self.model_combos.get(provider.name)
                    if combo_box:
                        # Find the index of the model
                        for i in range(combo_box.count()):
                            if combo_box.itemData(i) == model_to_select:
                                combo_box.setCurrentIndex(i)
                                return True
        return False

    def _create_model_change_handler(self, provider_name):
        """
        Create a handler for model selection change.

        Args:
            provider_name: The provider name to bind to the handler

        Returns:
            Handler function
        """

        def handler(idx):
            self.on_model_changed(idx, provider_name)

        return handler

    def create_model_menu_items(self, model_menu, parent_window):
        """
        Dynamically create model menu items from provider configuration.
        If a provider is missing an API key, show an "Add API Key" button instead of a dropdown.

        Args:
            model_menu: The QMenu to add model selection widgets to
            parent_window: Parent window for dialogs
        """
        providers = self.provider_config_loader.get_providers()

        if not providers:
            # No providers configured, show a message
            no_providers_label = QLabel("  No providers configured")
            no_providers_label.setFont(QFont("Consolas", 9))
            model_menu.addAction(QWidgetAction(parent_window))
            return

        # Check API keys for all providers
        api_key_manager = self._get_api_key_manager()

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

                # Set the default model only if this provider is currently active
                # Otherwise, keep it at placeholder to ensure only one active model
                if default_index > 0 and self.ai_client and self.ai_client.provider_name == provider.name:
                    model_combo.setCurrentIndex(default_index)

                # Connect change event
                handler = self._create_model_change_handler(provider.name)
                model_combo.currentIndexChanged.connect(handler)

                # Store the combo box for later access
                self.model_combos[provider.name] = model_combo

                provider_layout.addWidget(model_combo)
                provider_layout.addStretch()

                # Add the widget to the menu using QWidgetAction
                provider_action = QWidgetAction(parent_window)
                provider_action.setDefaultWidget(provider_widget)
                model_menu.addAction(provider_action)

                # Add "Delete API Key" action below the dropdown
                delete_key_action = QAction("      → Delete API Key", parent_window)

                # Use a closure-safe connection
                def make_delete_handler(prov, disp, parent):
                    def handler():
                        self.on_delete_api_key(prov, disp, parent)

                    return handler

                delete_key_action.triggered.connect(
                    make_delete_handler(provider.name, provider.display_name, parent_window)
                )
                model_menu.addAction(delete_key_action)
            else:
                # API key missing - show a clickable menu action instead of a button widget
                # First add the label as a widget
                provider_action = QWidgetAction(parent_window)
                provider_action.setDefaultWidget(provider_widget)
                model_menu.addAction(provider_action)

                # Then add a clickable "Add API Key" action
                add_key_action = QAction("      → Add API Key", parent_window)

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
            if self.message_handler:
                self.message_handler.append_message(
                    "System", "AI client not ready. Please wait for initialization to complete."
                )
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
        self._reset_other_provider_dropdowns(provider)

        # Switch to the selected provider and model
        self._switch_to_provider_model(provider, model, model_name)

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
                    # Save the API key
                    api_key_manager = self._get_api_key_manager()
                    api_key_manager.set_api_key(provider_name, api_key)

                    # Show success message
                    if self.message_handler:
                        self.message_handler.append_message(
                            "System", f"API key for {display_name} has been saved successfully!"
                        )

                    # Check if this is the first API key being added
                    is_first_key = not any(
                        api_key_manager.get_api_key(p.name)
                        for p in self.provider_config_loader.get_providers()
                        if p.name != provider_name
                    )

                    # Refresh the Model menu to show the dropdown instead of the button
                    self.refresh_model_menu(parent_window)

                    # If this is the first API key, automatically select a model from this provider
                    if is_first_key and self.ai_client:
                        self._select_first_available_provider()

                    # If AI client is not initialized yet, re-run prestart checks.
                    # check() will invoke the completion_callback internally when ready.
                    if not self.ai_client and self.prestart_checker:
                        status = self.prestart_checker.check()
                        if status == "ready" and self.enable_ai_mode_callback:
                            self.enable_ai_mode_callback()
        except Exception as e:
            self.logger.error(f"Error adding API key: {e}")
            if self.message_handler:
                self.message_handler.append_message("System", f"❌ Failed to add API key: {str(e)}")

    def on_delete_api_key(self, provider_name: str, display_name: str, parent_window):
        """
        Handle "Delete API Key" action click for a provider.

        Args:
            provider_name: Internal provider name (e.g., "openai", "fireworks")
            display_name: Display name for the provider (e.g., "OpenAI", "Fireworks")
            parent_window: Parent window for the dialog
        """
        try:
            from ..dialogs import show_confirmation_dialog

            # Show confirmation dialog
            confirmed = show_confirmation_dialog(
                parent_window,
                "Confirm Deletion",
                f"Are you sure you want to delete the API key for {display_name}?",
                default_no=True,
            )

            # If user did not confirm, return without deleting
            if not confirmed:
                return

            # Delete the API key
            api_key_manager = self._get_api_key_manager()
            api_key_manager.delete_api_key(provider_name)

            # Show success message
            if self.message_handler:
                self.message_handler.append_message(
                    "System", f"API key for {display_name} has been deleted successfully!"
                )

            # Check if the deleted key was for the active provider
            was_active_provider = self.ai_client and self.ai_client.provider_name == provider_name

            # If the AI client is using this provider, reset it
            if was_active_provider:
                self.ai_client.provider = None
                self.ai_client.provider_name = None

            # Refresh the Model menu to show "Add API Key" instead of the dropdown
            self.refresh_model_menu(parent_window)

            # If the deleted key was for the active provider, try to switch to another provider
            if was_active_provider:
                if not self._select_first_available_provider():
                    # No other providers with API keys found
                    if self.message_handler:
                        self.message_handler.append_message(
                            "System", "AI client reset. Please select a new provider and model."
                        )

        except Exception as e:
            self.logger.error(f"Error deleting API key: {e}")
            if self.message_handler:
                self.message_handler.append_message("System", f"❌ Failed to delete API key: {str(e)}")

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

    def restore_saved_model(self, provider: str, model: str):
        """
        Restore a saved model selection by applying it to the AI client.

        Args:
            provider: The provider name (e.g., "openai", "deepseek")
            model: The model identifier (e.g., "gpt-4o", "deepseek-chat")

        Returns:
            bool: True if restoration was successful, False otherwise
        """
        if not self.ai_client:
            self.logger.warn("Cannot restore model: AI client not initialized")
            return False

        # Get the combo box for this provider
        combo_box = self.model_combos.get(provider)
        if not combo_box:
            self.logger.warn(f"Cannot restore model: provider '{provider}' not found in menu")
            return False

        # Check if the model exists in the combo box
        model_index = None
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == model:
                model_index = i
                break

        if model_index is None or model_index == 0:
            self.logger.warn(f"Cannot restore model: model '{model}' not found for provider '{provider}'")
            return False

        # Get API key for this provider
        api_key = self._get_api_key_manager().get_api_key(provider)
        if not api_key:
            self.logger.warn(f"Cannot restore model: no API key for provider '{provider}'")
            return False

        # Initialize the provider
        new_provider = self._initialize_provider(provider, api_key)
        if not new_provider or not new_provider.is_available():
            self.logger.error(f"Failed to initialize provider for restoration: {provider}")
            return False

        # Update AI client
        self.ai_client.provider = new_provider
        self.ai_client.provider_name = provider
        self.ai_client.set_model(model)

        # Update dropdown to reflect the restored selection
        self._reset_other_provider_dropdowns(provider)

        # Set the current provider's dropdown to the saved model
        combo_box.blockSignals(True)
        combo_box.setCurrentIndex(model_index)
        combo_box.blockSignals(False)

        # Log the restoration
        self.logger.info(f"Restored saved model: {provider}/{model}")

        return True

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
        self._reset_other_provider_dropdowns(current_provider)

        # Find and select the matching model in the current provider's dropdown
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == current_model:
                # Block signals to avoid triggering on_model_changed
                combo_box.blockSignals(True)
                combo_box.setCurrentIndex(i)
                combo_box.blockSignals(False)
                return

        # If model not found in dropdown, it might be a custom model
        # Keep current dropdown selection as is
