"""Disk-based cache repository implementation."""

import json
import time
from pathlib import Path
from typing import Optional

from pyconflict.domain.repositories import ICacheRepository
from pyconflict.infrastructure.exceptions import CacheError


class DiskCacheRepository(ICacheRepository):
    """Disk-based cache implementation.

    Stores cache entries as JSON files with TTL support and LRU eviction.
    """

    def __init__(self, cache_dir: Path, max_size_mb: int = 100) -> None:
        """Initialize the disk cache.

        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum cache size in megabytes
        """
        self._cache_dir = cache_dir
        self._max_size_bytes = max_size_mb * 1024 * 1024

        # Create cache directory if it doesn't exist
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise CacheError(f"Failed to create cache directory: {e}")

    def get(self, key: str) -> Optional[dict]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value, or None if not found or expired
        """
        cache_file = self._get_cache_file(key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)

            # Check if expired
            if time.time() > data.get("expires_at", 0):
                cache_file.unlink()
                return None

            return data.get("value")

        except (json.JSONDecodeError, OSError):
            # Corrupted cache file - delete it
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None

    def set(self, key: str, value: dict, ttl: int) -> None:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds
        """
        cache_file = self._get_cache_file(key)

        data = {"value": value, "expires_at": time.time() + ttl}

        try:
            with open(cache_file, "w") as f:
                json.dump(data, f)

            # Check cache size and evict if needed
            self._evict_if_needed()

        except (OSError, TypeError) as e:
            raise CacheError(f"Failed to write cache: {e}")

    def clear(self) -> None:
        """Clear all cached values."""
        try:
            for cache_file in self._cache_dir.glob("*.json"):
                cache_file.unlink()
        except OSError as e:
            raise CacheError(f"Failed to clear cache: {e}")

    def _get_cache_file(self, key: str) -> Path:
        """Get the cache file path for a key.

        Args:
            key: Cache key

        Returns:
            Path to cache file
        """
        # Simple hash of key for filename
        filename = f"{hash(key)}.json"
        return self._cache_dir / filename

    def _get_cache_size(self) -> int:
        """Calculate total cache size in bytes.

        Returns:
            Cache size in bytes
        """
        total_size = 0
        try:
            for cache_file in self._cache_dir.glob("*.json"):
                total_size += cache_file.stat().st_size
        except OSError:
            pass
        return total_size

    def _evict_if_needed(self) -> None:
        """Evict oldest entries if cache exceeds max size.

        Uses LRU strategy - removes oldest accessed files first.
        """
        cache_size = self._get_cache_size()

        if cache_size <= self._max_size_bytes:
            return

        # Get all cache files sorted by access time (oldest first)
        try:
            cache_files = list(self._cache_dir.glob("*.json"))
            cache_files.sort(key=lambda f: f.stat().st_atime)

            # Remove oldest files until under limit
            for cache_file in cache_files:
                if cache_size <= self._max_size_bytes * 0.8:  # 80% threshold
                    break

                file_size = cache_file.stat().st_size
                cache_file.unlink()
                cache_size -= file_size

        except OSError:
            # If eviction fails, just continue
            pass
