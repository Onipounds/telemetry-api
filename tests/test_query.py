"""Query, filtering and listing tests."""

from tests.conftest import SAMPLE


def _seed(client):
    assert client.post("/api/readings", json=SAMPLE).status_code == 201


def test_query_all_orders_newest_first(client):
    _seed(client)
    rows = client.get("/api/readings").json()
    assert len(rows) == 4
    times = [r["ts"] for r in rows]
    assert times == sorted(times, reverse=True)


def test_filter_by_device_and_metric(client):
    _seed(client)
    rows = client.get("/api/readings", params={"device_id": "plc-01", "metric": "temp"}).json()
    assert len(rows) == 2
    assert {r["value"] for r in rows} == {50.0, 52.0}


def test_filter_by_time_window(client):
    _seed(client)
    rows = client.get(
        "/api/readings",
        params={"device_id": "plc-01", "since": "2024-01-01T00:00:30"},
    ).json()
    # only readings at/after 00:00:30
    assert all(r["ts"] >= "2024-01-01T00:00:30" for r in rows)


def test_limit(client):
    _seed(client)
    rows = client.get("/api/readings", params={"limit": 1}).json()
    assert len(rows) == 1


def test_list_devices(client):
    _seed(client)
    assert client.get("/api/devices").json() == ["plc-01", "plc-02"]


def test_latest_per_metric(client):
    _seed(client)
    rows = client.get("/api/devices/plc-01/latest").json()
    by_metric = {r["metric"]: r["value"] for r in rows}
    assert by_metric == {"temp": 52.0, "pressure": 4.0}  # newest temp, not 50.0
