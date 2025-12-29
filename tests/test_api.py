import pytest
from httpx import AsyncClient, ASGITransport
from metrics_server.app import app, store


@pytest.mark.asyncio
async def test_list_metrics_empty_initially():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/telemetry/ListMetrics")
        assert resp.status_code == 200
        assert resp.json() == {}


@pytest.mark.asyncio
async def test_get_metric_success():
    await store.update({
        "sw1": {"latency_ms": 1.5, "bandwidth_mbps": 7000}
    })

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/telemetry/GetMetric",
            params={"switch": "sw1", "metric": "latency_ms"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["switch"] == "sw1"
        assert body["metric"] == "latency_ms"
        assert body["value"] == 1.5
        assert "timestamp" in body


@pytest.mark.asyncio
async def test_get_metric_unknown_switch():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/telemetry/GetMetric",
            params={"switch": "unknown", "metric": "latency_ms"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_metric_unknown_metric():
    await store.update({
        "sw1": {"latency_ms": 1.0}
    })

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/telemetry/GetMetric",
            params={"switch": "sw1", "metric": "bandwidth_mbps"},
        )
        assert resp.status_code == 404
