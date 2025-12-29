"""
Simulated telemetry generator exposing switch metrics via HTTP.
"""

import os
import time
import random
import json
import threading
from flask import Flask, Response

app = Flask(__name__)

DEFAULT_SWITCH_COUNT = 4
DEFAULT_METRICS = ["bandwidth_mbps", "latency_ms", "packet_errors"]

UPDATE_INTERVAL_SEC = 10 # how often to refresh metrics
SPIKE_PROBABILITY = 0.1  # Probability (0–1) of simulating a temporary latency spike
ERROR_PROBABILITY = 0.1  # Probability (0–1) of introducing packet errors (rare in healthy networks)

# Allow port override via environment variable
SERVER_PORT = int(os.getenv("GENERATOR_PORT", 9001))
SERVER_HOST = os.getenv("GENERATOR_HOST", "127.0.0.1")


# -----------------------
# Configuration loading
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("Config file not found, using defaults")
        return {
            "switches": {"count": DEFAULT_SWITCH_COUNT},
            "metrics": DEFAULT_METRICS
        }

    with open(CONFIG_PATH) as f:
        return json.load(f)

config = load_config()


switch_cfg = config.get("switches", {})
SWITCH_COUNT = int(switch_cfg.get("count", DEFAULT_SWITCH_COUNT))

SWITCHES = {f"sw{i}" for i in range(1, SWITCH_COUNT + 1)}
METRICS = list(config.get("metrics", DEFAULT_METRICS))

state = {}
lock = threading.Lock()

def update_metrics():
    while True:
        new_state = {}
        for sw in SWITCHES:
            metrics_data = {}

            link_up = random.random() > 0.02

            for metric in METRICS:
                if metric == "link_status":
                    metrics_data[metric] = 1 if link_up else 0

                elif not link_up:
                    # Link is down → all operational counters are zero
                    metrics_data[metric] = 0

                elif metric == "bandwidth_mbps":
                    metrics_data[metric] = random.randint(6000, 10000)

                elif metric == "latency_ms":
                    latency = round(random.uniform(0.5, 2.0), 2)
                    # Simulate normal latency + rare spikes (10% chance)
                    if random.random() < SPIKE_PROBABILITY:
                        latency *= random.randint(5, 10)
                        latency = round(latency, 2)
                    metrics_data[metric] = latency

                elif metric == "packet_errors":
                    metrics_data[metric] = (
                    random.randint(1, 5)
                    if random.random() < ERROR_PROBABILITY
                        else 0
                    )

                elif metric == "tx_queue_depth":
                    metrics_data[metric] = random.randint(0, 1024)

                elif metric == "utilization_percent":
                    # Simulate link utilization (0–100%)
                    metrics_data[metric] = round(random.uniform(10.0, 95.0), 1)

                else:
                    metrics_data[metric] = 0

            new_state[sw] = metrics_data

        with lock:
            state.clear()
            state.update(new_state)

        time.sleep(UPDATE_INTERVAL_SEC)

@app.route("/counters", methods=["GET"])
def counters():
    with lock:
        rows = ["switch_id," + ",".join(METRICS)]
        for sw, metrics in state.items():
            row = [sw] + [str(metrics[m]) for m in METRICS]
            rows.append(",".join(row))
    return Response("\n".join(rows), mimetype="text/csv")

if __name__ == "__main__":
    threading.Thread(target=update_metrics, daemon=True).start()
    app.run(host=SERVER_HOST, port=SERVER_PORT)
