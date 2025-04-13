# src/managers/cache/joblib_cache_manager.py
import os
import joblib
import hashlib
import time
import json
from typing import Any, Optional, Dict, Callable, Tuple

from src.managers.cache.cache_manager import CacheManager
from src.core.logger_setup import get_logger


class JoblibCacheManager(CacheManager):
    """
    Implementation of CacheManager using joblib for file-based caching.
    """

    def __init__(self, cache_dir: str = "cache", enabled: bool = True):
        """
        Initialize the joblib cache manager.

        Args:
            cache_dir: Directory to store cache files
            enabled: Whether caching is enabled
        """
        self.logger = get_logger()
        self.cache_dir = cache_dir
        self.enabled = enabled

        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        self.logger.info(
            f"Initialized JoblibCacheManager with cache_dir={cache_dir}, enabled={enabled}")

    def _get_cache_path(self, key: str) -> str:
        """
        Generate the file path for a cache key.

        Args:
            key: The cache key

        Returns:
            The file path for the cache entry
        """
        # Create a hash of the key to use as filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.joblib")

    def get(self, key: str) -> Tuple[bool, Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to retrieve

        Returns:
            Tuple of (hit, value) where hit is a boolean indicating if the key was found,
            and value is the cached value (None if not found)
        """
        if not self.enabled:
            return False, None

        cache_path = self._get_cache_path(key)

        if os.path.exists(cache_path):
            try:
                cache_entry = joblib.load(cache_path)
                self.logger.debug(f"Cache hit for key: {key}")
                return True, cache_entry
            except Exception as e:
                self.logger.warning(f"Error loading cache for key {key}: {e}")

        self.logger.debug(f"Cache miss for key: {key}")
        return False, None

    def set(self, key: str, value: Any) -> bool:
        """
        Store a value in the cache.

        Args:
            key: The cache key to store
            value: The value to cache

        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(key)

        try:
            joblib.dump(value, cache_path)
            self.logger.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            self.logger.error(f"Error caching value for key {key}: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """
        Remove a specific key from the cache.

        Args:
            key: The cache key to remove

        Returns:
            Boolean indicating success
        """
        cache_path = self._get_cache_path(key)

        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                self.logger.debug(f"Invalidated cache for key: {key}")
                return True
            except Exception as e:
                self.logger.error(
                    f"Error invalidating cache for key {key}: {e}")

        return False

    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            Boolean indicating success
        """
        success = True

        try:
            # Get all .joblib files in the cache directory
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.joblib'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        self.logger.error(
                            f"Error removing cache file {file_path}: {e}")
                        success = False

            self.logger.info("Cleared all cache entries")
            return success
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False

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
        if not self.enabled:
            return func(*args, **kwargs)

        # Create a cache key from the function name and arguments
        # We serialize the arguments to JSON to ensure consistent keys
        try:
            func_name = func.__name__
            # Use a tuple to ensure args order is preserved
            args_str = json.dumps(args, sort_keys=True)
            # Sort kwargs by key for consistent ordering
            kwargs_str = json.dumps(kwargs, sort_keys=True)

            cache_key = f"{func_name}_{args_str}_{kwargs_str}"

            # Check cache
            hit, cached_result = self.get(cache_key)
            if hit:
                return cached_result

            # Cache miss, execute the function
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Cache the result
            self.set(cache_key, result)

            self.logger.debug(
                f"Executed and cached function {func_name} in {execution_time:.2f}s"
            )

            return result
        except Exception as e:
            self.logger.error(f"Error in cached_call: {e}")
            # Fall back to direct execution without caching
            return func(*args, **kwargs)
