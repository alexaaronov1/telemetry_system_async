# Telemetry Aggregation System

## Overview

This project implements a telemetry aggregation system inspired by NVIDIA UFM.

The system simulates telemetry metrics collected from a set of fabric switches, continuously ingests the data, stores the latest snapshot in memory, and exposes it through a REST API. Telemetry data is updated periodically and can be queried in real time by clients.

The implementation focuses on clear separation between telemetry generation, ingestion, data handling, and REST server integration.

---

## System Architecture

The system is composed of two independent services:

1. **Telemetry Generator**
2. **Metrics Server**

The telemetry generator simulates switches and exposes telemetry data over HTTP.
The metrics server periodically fetches this data, processes it, and serves it to clients via REST endpoints.

```
Telemetry Generator ──(CSV over HTTP)──► Metrics Server ──► REST API
```

---

## Telemetry Generation

The telemetry generator simulates a configurable number of network switches. Each switch periodically produces telemetry metrics such as bandwidth usage, latency, packet errors, and link-related indicators.

### System Operation

* Telemetry values are generated in memory at a fixed interval (default: 10 seconds)
* Metrics include simulated variability, such as latency spikes and occasional errors
* The generator maintains the latest telemetry values per switch

### Telemetry API

```
GET /counters
```

The endpoint returns a CSV matrix where:

* Each row represents a switch
* Each column represents a telemetry metric

This endpoint is consumed by the metrics server ingestion pipeline.

---

## Metrics Server

The metrics server is responsible for ingesting telemetry data, maintaining the latest aggregated snapshot, and serving this data through a REST API.

### System Operation

* At startup, the server launches an asynchronous ingestion task
* The ingestion task periodically fetches telemetry data from the generator
* Incoming CSV data is parsed and stored as an in-memory snapshot
* API requests read from the latest snapshot without triggering ingestion

Telemetry ingestion runs independently of client requests.

---

## Data Handling and Storage

Telemetry data is stored in memory as a snapshot representing the most recent state of all switches.

### Data flow

1. CSV telemetry is fetched from the generator
2. Values are parsed and converted into structured data
3. The entire snapshot is replaced atomically
4. API handlers read the current snapshot

Only the latest telemetry state is retained.

---

## REST API

The metrics server exposes the following REST endpoints:

### GetMetric

```
GET /telemetry/GetMetric?switch=<switch_id>&metric=<metric_name>
```

Returns the current value of a specific metric for a specific switch.

### ListMetrics

```
GET /telemetry/ListMetrics
```

Returns the full telemetry snapshot for all switches.

---

## Configuration

Each component has its own configuration file located under a dedicated `config/` directory.

### Telemetry Generator Configuration

Controls:

* Number of switches
* Supported telemetry metrics

Example:

```json
{
  "switches": { "count": 4 },
  "metrics": [
    "bandwidth_mbps",
    "latency_ms",
    "packet_errors"
  ]
}
```

### Metrics Server Configuration

Controls:

* Logging level

Example:

```json
{
  "logging": {
    "level": "INFO"
  }
}
```

If configuration files are not present, default values are used.

## Environment Variables

Both the telemetry generator and the metrics server support configuration via environment variables to control runtime settings such as network binding.

### Telemetry Generator

* `GENERATOR_HOST` — Host address to bind the telemetry generator (default: `127.0.0.1`)
* `GENERATOR_PORT` — Port to bind the telemetry generator (default: `9001`)

### Metrics Server

* `METRICS_SERVER_HOST` — Host address to bind the metrics server (default: `127.0.0.1`)
* `METRICS_SERVER_PORT` — Port to bind the metrics server (default: `8080`)
* `GENERATOR_HOST` — Host address of the telemetry generator (default: `127.0.0.1`)
* `GENERATOR_PORT` — Port of the telemetry generator (default: `9001`)

If environment variables are not set, default values are used.

---

## Observability

Basic logging is implemented in the metrics server to provide visibility into system behavior.
API request latency and ingestion activity are logged to help observe runtime behavior.

---

## Running the System

### Start the Telemetry Generator

```
python telemetry_generator/server.py
```

### Start the Metrics Server

```
uvicorn metrics_server.app:app --host 127.0.0.1 --port 8080
```

---

## Limitations

* In-memory storage
* Only the latest snapshot is retained (no history)
* Each server instance maintains its own state
* No persistence across restarts
* Scalability is limited by in-memory storage and per-process state

These tradeoffs were made to keep the implementation focused and simple.

---

## Possible Extensions

* Persist telemetry data to external storage
* Add historical data retention
* Support push-based telemetry ingestion
* Introduce distributed or shared storage
* Integrate external monitoring and metrics systems