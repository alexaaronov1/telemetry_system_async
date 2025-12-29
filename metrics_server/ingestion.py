"""
Async ingestion loop that periodically fetches telemetry data.
"""

import asyncio
import csv
import io
import logging
import httpx
from typing import Dict

INGEST_INTERVAL_SEC = 10
REQUEST_TIMEOUT_SEC = 2.0


async def ingest_loop(store, url: str) -> None:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SEC) as client:
        while True:
            try:
                resp = await client.get(url)
                resp.raise_for_status()

                reader = csv.DictReader(io.StringIO(resp.text))
                parsed: Dict[str, Dict[str, float]] = {}

                for row in reader:
                    sw = row.pop("switch_id")
                    parsed[sw] = {k: float(v) for k, v in row.items()}

                await store.update(parsed)

            except Exception as e:
                logging.error("[ingestion] failed to fetch telemetry: %s", e)

            await asyncio.sleep(INGEST_INTERVAL_SEC)


def start_ingestion(store, url: str) -> None:
    asyncio.create_task(ingest_loop(store, url))
