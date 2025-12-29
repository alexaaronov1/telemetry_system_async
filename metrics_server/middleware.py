"""
FastAPI middleware for basic observability.
"""

import time
import logging
from fastapi import Request


async def latency_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logging.info(
        "%s %s %d %.2fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
