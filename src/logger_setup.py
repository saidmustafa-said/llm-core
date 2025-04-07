# src/logger_setup.py

import logging
import threading
import os
from datetime import datetime


class Logger:
    _instance = None  # Singleton instance
    _initialized = False  # Ensure initialization happens only once

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, user_id=None, file_group=None):
        if not self._initialized:
            self.user_id = user_id
            self.file_group = file_group
            self.thread_local = threading.local()
            self._initialized = True

    def initialize_logging_context(self, user_id: str, file_group: str):
        """Initialize the logging context for the current thread."""
        self.user_id = user_id
        self.file_group = file_group
        self._setup_user_logger()

    def _setup_user_logger(self):
        """Set up a logger for the current thread's user_id and file group."""
        if not self.user_id or not self.file_group:
            raise ValueError("User ID and File Group must be set.")

        # Create directories if they don't exist
        user_log_dir = os.path.join('logs', str(self.user_id), self.file_group)
        os.makedirs(user_log_dir, exist_ok=True)

        # Generate a unique log filename based on the timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = os.path.join(user_log_dir, f"{timestamp}.log")

        # Setup logger
        logger_name = f"user_{self.user_id}_{self.file_group}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # 🔹 Remove all handlers (including root logger handlers)
        if logger.hasHandlers():
            logger.handlers.clear()

        # 🔹 Disable propagation to prevent logs from appearing in the root logger
        logger.propagate = False

        # Create a file handler that logs to the timestamped file
        file_handler = logging.FileHandler(log_filename)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'))

        logger.addHandler(file_handler)

        # Store logger in the thread-local context
        self.thread_local.logger = logger

        # 🔹 Ensure the root logger does NOT send logs to the console
        logging.getLogger().handlers.clear()

    def get_logger(self):
        """Get the logger for the current thread."""
        if not hasattr(self.thread_local, 'logger'):
            raise ValueError(
                "Logger not initialized. Call initialize_logging_context first.")
        return self.thread_local.logger


# Singleton instance of the Logger class
logger_instance = Logger()
