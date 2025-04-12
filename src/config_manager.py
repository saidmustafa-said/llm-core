import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from llamaapi import LlamaAPI

from src.managers.state.state_manager import StateManager
from src.managers.state.json_state_manager import JSONStateManager
from src.managers.history.history_manager import HistoryManager
from src.managers.history.json_history_manager import JSONHistoryManager


class ConfigManager:
    """
    Manages application configuration and selects appropriate backend implementations.
    Replaces the old config.py file with a centralized configuration management system.
    """
    _instance = None
    _is_initialized = False

    def __new__(cls, config_file: str = "config.json"):
        """Implement singleton pattern for ConfigManager."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the ConfigManager.

        Args:
            config_file: Path to the configuration file
        """
        # Only initialize once (singleton pattern)
        if not self._is_initialized:
            self.config_file = config_file
            self.config = self._load_config()

            # Set the project root directory in the config if not already set
            if not self.config.get("project_root_dir"):
                self.config["project_root_dir"] = os.path.abspath(
                    os.path.dirname(__file__))
                self.update_config(
                    {"project_root_dir": self.config["project_root_dir"]})

            # Load environment variables
            load_dotenv()

            # Initialize API client
            api_key = self.get_api_key()
            self.llama_api = LlamaAPI(api_key) if api_key else None

            # Initialize common path variables
            self.root_dir = self.get_root_dir()
            self.tags_list_path = self.get_tags_list_path()
            self.category_subcategory_list_path = self.get_category_subcategory_path()
            self.dataset_path = self.get_dataset_path()

            # Mark as initialized
            self._is_initialized = True
            # self.logger = get_logger()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "environment": "development",
            "state_backend": "json",
            "history_backend": "json",
            "sessions_dir": "sessions",
            "history_dir": "chat_history",
            "project_root_dir": os.path.abspath(os.path.dirname(__file__)),
            "data_paths": {
                "tags_list": "data/tags.csv",
                "category_subcategory_list": "data/category_subcategory.csv",
                "dataset": "data/dataset.csv"
            },
            "api_key_env_var": "apiKey"
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

    # Path management methods
    def get_root_dir(self) -> str:
        """Get the project root directory path."""
        return self.config.get("project_root_dir")

    def get_data_path(self, path_key: str) -> str:
        """
        Get the full path to a data file based on its config key.
        
        Args:
            path_key: Key in the data_paths config section
            
        Returns:
            Full path to the data file
        """
        data_paths = self.config.get("data_paths", {})
        relative_path = data_paths.get(path_key)

        if not relative_path:
            raise ValueError(
                f"Path for '{path_key}' not found in configuration")

        return os.path.join(self.get_root_dir(), relative_path)

    def get_api_key(self) -> str:
        """Get the API key from environment variables."""
        env_var = self.config.get("api_key_env_var", "apiKey")
        return os.getenv(env_var)

    # Convenience methods for common paths
    def get_tags_list_path(self) -> str:
        """Get the path to the tags list CSV file."""
        return self.get_data_path("tags_list")

    def get_category_subcategory_path(self) -> str:
        """Get the path to the category subcategory CSV file."""
        return self.get_data_path("category_subcategory_list")

    def get_dataset_path(self) -> str:
        """Get the path to the dataset CSV file."""
        return self.get_data_path("dataset")

    def get_llama_api(self) -> LlamaAPI:
        """Get the initialized LlamaAPI instance."""
        return self.llama_api
