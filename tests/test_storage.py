import pytest
import asyncio
from metrics_server.storage import TelemetryStore


@pytest.mark.asyncio
async def test_storage_update_and_snapshot():
    store = TelemetryStore()

    data = {
        "sw1": {"latency_ms": 1.2, "bandwidth_mbps": 5000},
        "sw2": {"latency_ms": 2.3, "bandwidth_mbps": 6000},
    }

    await store.update(data)
    snapshot = await store.snapshot()

    assert "sw1" in snapshot
    assert "sw2" in snapshot
    assert snapshot["sw1"]["latency_ms"] == 1.2
    assert snapshot["sw2"]["bandwidth_mbps"] == 6000
    assert "timestamp" in snapshot["sw1"]


@pytest.mark.asyncio
async def test_storage_overwrites_snapshot_atomically():
    store = TelemetryStore()

    first = {"sw1": {"latency_ms": 1.0}}
    second = {"sw1": {"latency_ms": 5.0}}

    await store.update(first)
    snap1 = await store.snapshot()

    await store.update(second)
    snap2 = await store.snapshot()

    assert snap1["sw1"]["latency_ms"] == 1.0
    assert snap2["sw1"]["latency_ms"] == 5.0
