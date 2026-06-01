"""Tests for the /api/alerts endpoint (readings over a threshold)."""
from tests.conftest import SAMPLE


def _seed(client):
    assert client.post("/api/readings", json=SAMPLE).status_code == 201


def test_alerts_returns_only_readings_over_threshold(client):
    _seed(client)
    rows = client.get("/api/alerts", params={"threshold": 40, "metric": "temp"}).json()
    # temps are 50.0, 52.0, 20.0 -> only the two above 40 come back
    assert {r["value"] for r in rows} == {50.0, 52.0}


def test_alerts_orders_worst_first(client):
    _seed(client)
    rows = client.get("/api/alerts", params={"threshold": 40, "metric": "temp"}).json()
    values = [r["value"] for r in rows]
    assert values == sorted(values, reverse=True)  # highest first


def test_alerts_threshold_is_required(client):
    _seed(client)
    # no threshold given -> FastAPI rejects it with 422
    assert client.get("/api/alerts").status_code == 422