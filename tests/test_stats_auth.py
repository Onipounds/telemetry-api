"""Aggregation and authentication tests."""

import importlib

from fastapi.testclient import TestClient

from tests.conftest import SAMPLE


def test_stats(client):
    client.post("/api/readings", json=SAMPLE)
    s = client.get("/api/stats", params={"device_id": "plc-01", "metric": "temp"}).json()
    assert s["count"] == 2
    assert s["min"] == 50.0
    assert s["max"] == 52.0
    assert s["avg"] == 51.0
    assert s["first_ts"] is not None and s["last_ts"] is not None


def test_stats_empty_is_zero(client):
    s = client.get("/api/stats", params={"device_id": "nope", "metric": "temp"}).json()
    assert s["count"] == 0
    assert s["avg"] is None


def test_api_key_required_when_configured(tmp_path, monkeypatch):
    db_file = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("API_KEY", "secret-token")

    from telemetry_api import db as db_mod
    db_mod.init_engine(f"sqlite:///{db_file}")
    app = importlib.import_module("telemetry_api.app").create_app()
    c = TestClient(app)

    # write without key -> 401
    assert c.post("/api/readings", json=SAMPLE).status_code == 401
    # write with wrong key -> 401
    assert c.post("/api/readings", json=SAMPLE, headers={"X-API-Key": "nope"}).status_code == 401
    # write with correct key -> 201
    ok = c.post("/api/readings", json=SAMPLE, headers={"X-API-Key": "secret-token"})
    assert ok.status_code == 201
    # reads stay open
    assert c.get("/api/devices").status_code == 200
