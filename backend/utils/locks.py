"""
Async lock manager to prevent race conditions.
Ensures only one request fetches data for a given symbol at a time.
"""

import asyncio
from typing import Dict


class LockManager:
    """
    Manages per-symbol async locks to prevent duplicate concurrent
    data fetches for the same symbol.
    """

    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
        self._meta_lock = asyncio.Lock()

    async def acquire(self, key: str) -> asyncio.Lock:
        """
        Get or create a lock for the given key.
        
        Usage:
            lock = await lock_manager.acquire("BTCUSDT")
            async with lock:
                # fetch data
        """
        async with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]

    async def cleanup(self) -> None:
        """Remove locks that are not currently held."""
        async with self._meta_lock:
            unlocked = [
                k for k, lock in self._locks.items()
                if not lock.locked()
            ]
            for key in unlocked:
                del self._locks[key]


# Global lock manager instance
lock_manager = LockManager()
