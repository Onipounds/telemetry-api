"""Shared fixtures: a fresh temporary database and a test client per test."""

import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A TestClient backed by an isolated SQLite file under tmp_path."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.delenv("API_KEY", raising=False)

    # rebuild engine + app against the patched environment
    from telemetry_api import db as db_mod
    db_mod.init_engine(f"sqlite:///{db_file}")
    app_mod = importlib.import_module("telemetry_api.app")
    app = app_mod.create_app()

    with TestClient(app) as c:
        yield c


SAMPLE = [
    {"device_id": "plc-01", "metric": "temp", "value": 50.0, "ts": "2024-01-01T00:00:00"},
    {"device_id": "plc-01", "metric": "temp", "value": 52.0, "ts": "2024-01-01T00:01:00"},
    {"device_id": "plc-01", "metric": "pressure", "value": 4.0, "ts": "2024-01-01T00:01:00"},
    {"device_id": "plc-02", "metric": "temp", "value": 20.0, "ts": "2024-01-01T00:02:00"},
]
