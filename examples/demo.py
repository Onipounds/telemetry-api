"""Self-contained demo: spin up the app in-process, post telemetry, query it.

    python examples/demo.py

Uses a throwaway SQLite file so it runs anywhere with no server to start.
"""

import os
import tempfile
from datetime import datetime, timedelta, timezone

# point at a temp DB before importing the app
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

from fastapi.testclient import TestClient  # noqa: E402

from telemetry_api.app import create_app  # noqa: E402

client = TestClient(create_app())


def main() -> None:
    # generate a few minutes of two metrics for one device
    now = datetime.now(timezone.utc)
    batch = []
    for i in range(10):
        ts = (now - timedelta(minutes=10 - i)).isoformat()
        batch.append({"device_id": "plc-01", "metric": "temp", "value": 50 + i * 0.5, "ts": ts})
        batch.append({"device_id": "plc-01", "metric": "pressure", "value": 4.0 + i * 0.1, "ts": ts})

    print("POST /api/readings ->", client.post("/api/readings", json=batch).json())
    print("GET  /api/devices  ->", client.get("/api/devices").json())

    latest = client.get("/api/devices/plc-01/latest").json()
    print("GET  /latest       ->", {r["metric"]: r["value"] for r in latest})

    stats = client.get("/api/stats", params={"device_id": "plc-01", "metric": "temp"}).json()
    print("GET  /api/stats    ->", stats)

    recent = client.get("/api/readings", params={"device_id": "plc-01", "limit": 3}).json()
    print(f"GET  /api/readings -> {len(recent)} most-recent rows")


if __name__ == "__main__":
    main()
    os.unlink(_tmp.name)
