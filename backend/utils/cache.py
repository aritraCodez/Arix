"""
In-memory TTL (Time-To-Live) cache.
Provides fast caching without external dependencies like Redis.
"""

import time
import threading
from typing import Any


class TTLCache:
    """Thread-safe in-memory cache with per-key TTL expiration."""

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """
        Get a value from cache if it exists and hasn't expired.
        Returns None if key is missing or expired.
        """
        with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        """
        Set a value in cache with TTL in seconds.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds
        """
        with self._lock:
            self._store[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        """Remove a key from cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._store.clear()

    def cleanup(self) -> None:
        """Remove all expired entries from cache."""
        now = time.time()
        with self._lock:
            expired_keys = [
                k for k, (_, expires_at) in self._store.items()
                if now > expires_at
            ]
            for key in expired_keys:
                del self._store[key]

    @property
    def size(self) -> int:
        """Number of entries in cache (including potentially expired ones)."""
        return len(self._store)


# Global cache instance
cache = TTLCache()
