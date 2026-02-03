"""
UI Configuration Manager - Persists user interface selections
Saves menu selections to .forshape/ui_config.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class UIConfigManager:
    """Manages persistent UI configuration settings"""

    CONFIG_FILENAME = "ui_config.json"

    def __init__(self, forshape_dir: Path):
        """
        Initialize UI config manager

        Args:
            forshape_dir: Path to .forshape directory
        """
        self.forshape_dir = forshape_dir
        self.config_path = forshape_dir / self.CONFIG_FILENAME
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """
        Load UI configuration from file

        Returns:
            Dict with UI settings, or empty dict if file doesn't exist
        """
        if not self.config_path.exists():
            logger.info(f"No UI config file found at {self.config_path}")
            self._config = {}
            return self._config

        try:
            with open(self.config_path, encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Loaded UI config from {self.config_path}")
            return self._config
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load UI config: {e}")
            self._config = {}
            return self._config

    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save UI configuration to file

        Args:
            config: Dict with UI settings to save

        Returns:
            True if successful, False otherwise
        """
        self._config = config

        try:
            # Ensure directory exists
            self.forshape_dir.mkdir(parents=True, exist_ok=True)

            # Write config file
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved UI config to {self.config_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to save UI config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """Set a config value and save"""
        self._config[key] = value
        return self.save(self._config)

    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple config values and save"""
        self._config.update(updates)
        return self.save(self._config)
