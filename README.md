# Telemetry Aggregation System (Async / FastAPI)

## Overview

This project implements a **production-oriented network telemetry aggregation system**, inspired by NVIDIA UFM.

The system continuously ingests telemetry metrics from a set of simulated fabric switches and serves the **latest aggregated snapshot** via a REST API.
The design is **async-first**, **non-blocking**, and suitable for handling **many concurrent clients**.

The solution is intentionally lightweight but demonstrates correct architectural reasoning around **ingestion pipelines, data freshness, concurrency, and failure isolation**.

---

## High-Level Architecture

The system consists of **two decoupled components**:

1. **Telemetry Generator** – simulates switches and exposes raw telemetry data.
2. **Metrics Server** – ingests telemetry asynchronously and serves it via a REST API.

```
Telemetry Generator  ──►  Async Ingestion Pipeline  ──►  In-Memory Snapshot  ──►  REST API
        (CSV)                    (background task)          (async-safe)        (FastAPI)
```

Telemetry ingestion runs **continuously and independently of client requests**.

---

## Telemetry Generator

### Purpose

The telemetry generator simulates fabric switches producing telemetry metrics.
It represents an **external dependency** from the perspective of the metrics server.

### Behavior

* Generates telemetry for a configurable number of switches.
* Simulates realistic behavior:

  * bandwidth usage
  * latency spikes
  * packet errors
  * link down scenarios
* Updates telemetry periodically (default: every 10 seconds).

### Interface

```
GET /counters
```

Returns telemetry data as a **CSV matrix**:

* Rows represent switches
* Columns represent metrics

### Notes

* The generator runs independently of client traffic.
* It is intentionally kept simple and unchanged between versions.
* Async concerns are handled entirely by the consumer (metrics server).

---

## Metrics Server (Core System)

The metrics server is the **production-facing component**.

### Key Design Goals

* Non-blocking request handling
* Continuous ingestion independent of API traffic
* Safe shared state under concurrency
* Predictable behavior under load
* Clear lifecycle management

---

## Async Ingestion Pipeline

* Runs as an **async background task**.
* Started at application startup using **FastAPI lifespan events**.
* Uses `httpx.AsyncClient` for non-blocking HTTP I/O.
* Applies explicit timeouts.
* Polls the telemetry generator at a fixed interval.

### Key Properties

* Ingestion is **not request-driven**.
* Failures in ingestion do **not** impact API availability.
* The system always serves the **latest successfully ingested snapshot**.

---

## In-Memory Storage

* Stores only the **latest telemetry snapshot**.
* Protected by an explicit `asyncio.Lock`.
* Ensures consistency under concurrent async access.

### Concurrency Model

* **Writes**: performed by the ingestion task.
* **Reads**: performed by API handlers.
* Both use async locking for correctness and clarity.

This design favors **correctness and explicit intent** over micro-optimizations.

---

## REST API

### Endpoints

#### GetMetric

```
GET /telemetry/GetMetric?switch=<switch_id>&metric=<metric_name>
```

Returns the current value of a specific metric for a specific switch.

#### ListMetrics

```
GET /telemetry/ListMetrics
```

Returns the full telemetry snapshot for all switches.

### Characteristics

* Fully asynchronous endpoints.
* No blocking I/O.
* Constant-time in-memory reads.
* Safe under high concurrency.

---

## Observability

Basic observability is implemented via FastAPI middleware:

* Measures end-to-end request latency.
* Logs request path, status code, and duration.
* Uses standard Python logging.

This satisfies observability requirements without introducing heavy dependencies.

---

## Configuration

### Environment Variables

#### Metrics Server

* `METRICS_SERVER_HOST` (default: `127.0.0.1`)
* `METRICS_SERVER_PORT` (default: `8080`)
* `GENERATOR_HOST` (default: `127.0.0.1`)
* `GENERATOR_PORT` (default: `9001`)

#### Telemetry Generator

* `GENERATOR_PORT` (default: `9001`)
* `GENERATOR_HOST` (optional)

### Configuration Files

* Generator config controls:

  * number of switches
  * supported metrics
* Metrics server config controls:

  * log level

If configuration files are missing, **sane defaults are used**.

---

## Running the System

### 1. Start the Telemetry Generator

```
python telemetry_generator/server.py
```

### 2. Start the Metrics Server

```
uvicorn metrics_server.app:app --host 0.0.0.0 --port 8080
```

For higher concurrency:

```
uvicorn metrics_server.app:app --workers 4
```

---

## Performance Characteristics

* API requests are served from in-memory state.
* No network calls on the request path.
* Latency is stable and predictable.
* Scales efficiently with concurrent clients.

---

## Failure Modes and Isolation

* Telemetry generator failure:

  * ingestion logs errors
  * API continues serving last snapshot
* Slow generator:

  * bounded by request timeout
* High API load:

  * ingestion unaffected

Failures are intentionally **isolated by design**.

---

## Limitations

* In-memory storage is per-process.
* Each worker maintains its own snapshot.
* No historical retention.
* No persistence across restarts.

These tradeoffs are intentional for simplicity.

---

## Future Improvements

* Shared external storage (Redis, database).
* Historical metrics retention.
* Push-based ingestion instead of polling.
* Distributed ingestion pipelines.
* Advanced observability (Prometheus, tracing).