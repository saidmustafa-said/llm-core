# src/managers/flow/handlers/base_handler.py

from typing import Dict, Any
from src.managers.state.state_manager import StateManager
from src.managers.history.history_manager import HistoryManager
from src.logger_setup import get_logger


class BaseHandler:
    """
    Base class for state handlers that provides common functionality.
    """

    def __init__(self, state_manager: StateManager, history_manager: HistoryManager):
        """
        Initialize the base handler with state and history managers.

        Args:
            state_manager: Manager for storing and retrieving session state
            history_manager: Manager for logging conversation history
        """
        self.state_manager = state_manager
        self.history_manager = history_manager
        self.logger = get_logger()
