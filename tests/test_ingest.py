"""Ingestion and validation tests."""

from tests.conftest import SAMPLE


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ingest_batch(client):
    r = client.post("/api/readings", json=SAMPLE)
    assert r.status_code == 201
    assert r.json() == {"ingested": 4}


def test_ingest_fills_timestamp_when_omitted(client):
    r = client.post("/api/readings", json=[{"device_id": "d", "metric": "m", "value": 1.0}])
    assert r.status_code == 201
    rows = client.get("/api/readings", params={"device_id": "d"}).json()
    assert rows[0]["ts"] is not None


def test_ingest_rejects_empty_batch(client):
    r = client.post("/api/readings", json=[])
    assert r.status_code == 422


def test_ingest_rejects_bad_payload(client):
    # missing value, blank device_id
    r = client.post("/api/readings", json=[{"device_id": "", "metric": "m"}])
    assert r.status_code == 422
