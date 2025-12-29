"""
Async in-memory storage for the latest telemetry snapshot.
"""

import asyncio
import time
from typing import Dict, Any


class TelemetryStore:
    def __init__(self):
        self._snapshot: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def update(self, data: Dict[str, Dict[str, float]]) -> None:
        ts = int(time.time())
        new_snapshot = {
            sw: {**metrics, "timestamp": ts}
            for sw, metrics in data.items()
        }
        async with self._lock:
            self._snapshot = new_snapshot

    async def snapshot(self) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            return self._snapshot
