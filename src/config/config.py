import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from llamaapi import LlamaAPI

from src.managers.state.state_manager import StateManager
from src.managers.state.json_state_manager import JSONStateManager
from src.managers.history.history_manager import HistoryManager
from src.managers.history.json_history_manager import JSONHistoryManager
from src.managers.cache.cache_manager import CacheManager
from src.managers.cache.joblib_cache_manager import JoblibCacheManager


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
        if not self._is_initialized:
            self.config_file = config_file
            self.config = self._load_config()
            self._set_default_project_root()
            load_dotenv()

            # Initialize backend services
            self.llama_api = self._initialize_llama_api()
            self.root_dir = self.get_root_dir()
            self.dataset_path = self.get_dataset_path()

            self._is_initialized = True

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = self._get_default_config()
        return self._load_or_create_config(default_config)

    def _get_default_config(self) -> Dict[str, Any]:
        """Return the default configuration."""
        return {
            "environment": "development",
            "state_backend": "json",
            "history_backend": "json",
            "cache_backend": "joblib",
            "cache_enabled": True,
            "sessions_dir": "sessions",
            "history_dir": "chat_history",
            "cache_dir": "cache",
            "project_root_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
            "data_paths": {
                "dataset": "data/dataset.csv"
            },
            "api_key_env_var": "apiKey"
        }

    def _load_or_create_config(self, default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Try loading config from file, if it fails create the file with default values."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Error loading config file: {e}")
        else:
            self._create_default_config_file(default_config)

        return default_config

    def _create_default_config_file(self, default_config: Dict[str, Any]) -> None:
        """Create a new config file with default values."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Error creating default config file: {e}")

    def _set_default_project_root(self) -> None:
        """Set project root directory if not already set in config."""
        if not self.config.get("project_root_dir"):
            self.config["project_root_dir"] = os.path.abspath(
                os.path.dirname(__file__))
            self.update_config(
                {"project_root_dir": self.config["project_root_dir"]})

    def _initialize_llama_api(self) -> LlamaAPI:
        """Initialize LlamaAPI client with the API key."""
        api_key = self.get_api_key()
        return LlamaAPI(api_key) if api_key else None

    def get_state_manager(self) -> StateManager:
        """Return the appropriate StateManager implementation."""
        backend = self.config.get("state_backend", "json")
        return self._get_manager(StateManager, backend, "sessions_dir", JSONStateManager)

    def get_history_manager(self) -> HistoryManager:
        """Return the appropriate HistoryManager implementation."""
        backend = self.config.get("history_backend", "json")
        return self._get_manager(HistoryManager, backend, "history_dir", JSONHistoryManager)

    def get_cache_manager(self) -> CacheManager:
        """Return the appropriate CacheManager implementation."""
        backend = self.config.get("cache_backend", "joblib")
        enabled = self.config.get("cache_enabled", True)
        return self._get_cache_manager(backend, enabled)

    def _get_manager(self, manager_type, backend: str, dir_key: str, default_manager):
        """Helper method to return the appropriate manager based on backend."""
        if backend == "json":
            return default_manager(self.config.get(dir_key, "sessions"))
        else:
            # Extend for other backends (e.g., Redis, Postgres) in the future
            return default_manager(self.config.get(dir_key, "sessions"))

    def _get_cache_manager(self, backend: str, enabled: bool) -> CacheManager:
        """Helper method to return the appropriate cache manager."""
        if backend == "joblib":
            return JoblibCacheManager(self.config.get("cache_dir", "cache"), enabled=enabled)
        else:
            # Extend for other backends (e.g., Redis) in the future
            return JoblibCacheManager(self.config.get("cache_dir", "cache"), enabled=enabled)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration values and save to file."""
        self.config.update(updates)
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False

    # Path management methods
    def get_root_dir(self) -> str:
        """Get the project root directory path."""
        return self.config.get("project_root_dir")

    def get_data_path(self, path_key: str) -> str:
        """Get the full path to a data file based on its config key."""
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

    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.config.get("cache_enabled", True)

    def enable_caching(self, enabled: bool = True) -> None:
        """Enable or disable caching."""
        self.config["cache_enabled"] = enabled
        self.update_config({"cache_enabled": enabled})

    # Convenience methods for common paths
    def get_dataset_path(self) -> str:
        """Get the path to the dataset CSV file."""
        return self.get_data_path("dataset")

    def get_llama_api(self) -> LlamaAPI:
        """Get the initialized LlamaAPI instance."""
        return self.llama_api
