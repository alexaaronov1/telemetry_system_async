"""
FastAPI application serving aggregated telemetry metrics.
"""

import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from .storage import TelemetryStore
from .ingestion import start_ingestion
from .middleware import latency_middleware

DEFAULT_LOG_LEVEL = "INFO"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"logging": {"level": DEFAULT_LOG_LEVEL}}
    with open(CONFIG_PATH) as f:
        return json.load(f)


config = load_config()
logging.basicConfig(
    level=getattr(logging, config["logging"]["level"], logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
)

store = TelemetryStore()

GENERATOR_HOST = os.getenv("GENERATOR_HOST", "127.0.0.1")
GENERATOR_PORT = int(os.getenv("GENERATOR_PORT", 9001))
SOURCE_URL = f"http://{GENERATOR_HOST}:{GENERATOR_PORT}/counters"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_ingestion(store, SOURCE_URL)
    yield
    # Shutdown (cleanup hooks would go here)


app = FastAPI(lifespan=lifespan)
app.middleware("http")(latency_middleware)


@app.get("/telemetry/GetMetric")
async def get_metric(switch: str, metric: str):
    snapshot = await store.snapshot()

    if switch not in snapshot:
        raise HTTPException(status_code=404, detail="switch not found")

    if metric not in snapshot[switch]:
        raise HTTPException(status_code=404, detail="metric not found")

    return {
        "switch": switch,
        "metric": metric,
        "value": snapshot[switch][metric],
        "timestamp": snapshot[switch]["timestamp"],
    }


@app.get("/telemetry/ListMetrics")
async def list_metrics():
    return await store.snapshot()
