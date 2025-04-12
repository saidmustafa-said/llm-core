# src/managers/cache/cache_manager.py
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, Callable, Tuple


class CacheManager(ABC):
    """
    Abstract base class for caching implementations.
    Defines the interface that all cache implementations must follow.
    """

    @abstractmethod
    def get(self, key: str) -> Tuple[bool, Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            Tuple of (hit, value) where hit is a boolean indicating if the key was found,
            and value is the cached value (None if not found)
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """
        Store a value in the cache.

        Args:
            key: The cache key to store
            value: The value to cache

        Returns:
            Boolean indicating success
        """
        pass

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """
        Remove a specific key from the cache.

        Args:
            key: The cache key to remove

        Returns:
            Boolean indicating success
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            Boolean indicating success
        """
        pass

    @abstractmethod
    def cached_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with caching. If the function has been called with
        the same arguments before, return the cached result instead of executing
        the function again.

        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function result (either from cache or fresh execution)
        """
        pass
