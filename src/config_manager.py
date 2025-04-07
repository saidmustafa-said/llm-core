# config_manager.py

import os
import json
from typing import Dict, Any, Optional

from src.managers.state.state_manager import StateManager
from src.managers.state.json_state_manager import JSONStateManager
from src.managers.history.history_manager import HistoryManager
from src.managers.history.json_history_manager import JSONHistoryManager


class ConfigManager:
    """
    Manages application configuration and selects appropriate backend implementations.
    """

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the ConfigManager.

        Args:
            config_file: Path to the configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()
        # self.logger = get_logger()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "environment": "development",
            "state_backend": "json",
            "history_backend": "json",
            "sessions_dir": "sessions",
            "history_dir": "chat_history",
        }

        # Try to load from file
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Error loading config file: {str(e)}")
                return default_config
        else:
            # Create default config file
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)
            except Exception as e:
                print(f"Error creating default config file: {str(e)}")

            return default_config

    def get_state_manager(self) -> StateManager:
        """
        Get the appropriate StateManager implementation based on configuration.

        Returns:
            An instance of StateManager
        """
        backend = self.config.get("state_backend", "json")

        if backend == "json":
            return JSONStateManager(self.config.get("sessions_dir", "sessions"))
        elif backend == "redis":
            # For future implementation
            # self.logger.warning(
            #     "Redis state manager not implemented yet, falling back to JSON")
            return JSONStateManager(self.config.get("sessions_dir", "sessions"))
        else:
            # self.logger.warning(
            #     f"Unknown state backend: {backend}, using JSON")
            return JSONStateManager(self.config.get("sessions_dir", "sessions"))

    def get_history_manager(self) -> HistoryManager:
        """
        Get the appropriate HistoryManager implementation based on configuration.

        Returns:
            An instance of HistoryManager
        """
        backend = self.config.get("history_backend", "json")

        if backend == "json":
            return JSONHistoryManager(self.config.get("history_dir", "chat_history"))
        elif backend == "postgres":
            # For future implementation
            # self.logger.warning(
            #     "Postgres history manager not implemented yet, falling back to JSON")
            return JSONHistoryManager(self.config.get("history_dir", "chat_history"))
        else:
            # self.logger.warning(
            #     f"Unknown history backend: {backend}, using JSON")
            return JSONHistoryManager(self.config.get("history_dir", "chat_history"))

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration values.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            True if successful, False otherwise
        """
        self.config.update(updates)

        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            # self.logger.error(f"Error updating config file: {str(e)}")
            return False
