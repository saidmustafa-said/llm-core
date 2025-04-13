# src/logger_setup.py
import logging
import threading
import os
from pathlib import Path
from typing import Optional


class SessionLogger:
    """Centralized per-session logging with thread-safe initialization"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._setup()
        return cls._instance

    def _setup(self):
        """Initialize base logger configuration"""
        self._local = threading.local()
        self._log_dir = Path("logs")
        # Ensure base logs directory exists
        self._log_dir.mkdir(exist_ok=True, parents=True)
        # Configure root logger to prevent unwanted outputs
        logging.getLogger().handlers = []

        # Setup health check logger
        self._setup_health_check_logger()

    def _setup_health_check_logger(self):
        """Setup dedicated logger for health checks"""
        health_check_logger = logging.getLogger("health_check")
        health_check_logger.setLevel(logging.INFO)

        # Clear existing handlers
        for handler in health_check_logger.handlers[:]:
            health_check_logger.removeHandler(handler)

        # Create health check log file
        health_check_file = self._log_dir / "health_checks.log"
        file_handler = logging.FileHandler(health_check_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s'
        ))
        health_check_logger.addHandler(file_handler)

        self.health_check_logger = health_check_logger

    def start_session(self, user_id: str, session_id: str):
        """Initialize a new logging session"""
        # Create user-specific directory (with parents if needed)
        user_dir = self._log_dir / user_id
        user_dir.mkdir(exist_ok=True, parents=True)

        # Single log file per session
        log_file = user_dir / f"{session_id}.log"

        # Configure logger
        logger = logging.getLogger(f"user.{user_id}.session.{session_id}")
        logger.setLevel(logging.DEBUG)

        # Only clear handlers and add new file handler if the logger doesn't have any handlers
        if not logger.handlers:
            # File handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s'
            ))
            logger.addHandler(file_handler)

        # Store in thread-local storage
        self._local.logger = logger

    def get_logger(self) -> logging.Logger:
        """Get the current session's logger"""
        if not hasattr(self._local, 'logger'):
            # Fallback to system logger if no session initialized
            system_logger = logging.getLogger("system")
            if not system_logger.handlers:
                system_logger.addHandler(logging.StreamHandler())
                system_logger.setLevel(logging.WARNING)
            return system_logger
        return self._local.logger

    def get_health_check_logger(self) -> logging.Logger:
        """Get the dedicated health check logger"""
        return self.health_check_logger


# Global instance
session_logger = SessionLogger()

# Shortcut for cleaner imports


def get_logger() -> logging.Logger:
    return session_logger.get_logger()


def get_health_check_logger() -> logging.Logger:
    return session_logger.get_health_check_logger()
