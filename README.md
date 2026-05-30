# telemetry-api

A small, production-shaped **FastAPI** service for ingesting and querying
sensor telemetry. It accepts batches of device readings, stores them in a
database via **SQLAlchemy**, and serves them back with filtering, latest-value
lookups, and aggregate statistics.

It's the natural companion to a device-side collector (for example, the
[s7-live-monitor](https://github.com/Onipounds/s7-live-monitor) reads tags off a
PLC; this is the service it would POST them to).

## Why it's built this way

The code is split into clear layers so each part is testable on its own and the
web layer stays thin:

```
src/telemetry_api/
  config.py     # settings from environment
  db.py         # engine, session factory, FastAPI session dependency
  models.py     # SQLAlchemy ORM model (indexed for time-range queries)
  schemas.py    # Pydantic request/response models (validation)
  crud.py       # all database queries, isolated from the API
  app.py        # FastAPI routes wiring the above together
```

This separation (schemas vs models vs data-access vs routes) is the part worth
looking at: the route handlers contain almost no logic, and every query in
`crud.py` is covered by tests using an isolated database.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | liveness check |
| POST | `/api/readings` | ingest a batch of readings (auth, if configured) |
| GET | `/api/readings` | query with `device_id`, `metric`, `since`, `until`, `limit` |
| GET | `/api/devices` | list known device ids |
| GET | `/api/devices/{id}/latest` | latest reading per metric for a device |
| GET | `/api/stats` | count / min / max / avg over a device + metric |

Requests are validated by Pydantic; bad payloads get a `422` automatically.
Interactive docs are served at `/docs`.

## Run it

```bash
pip install -e ".[dev]"
uvicorn telemetry_api.app:app --reload      # http://localhost:8000/docs
python examples/demo.py                     # self-contained end-to-end demo
pytest -v                                   # 14 tests
```

Ingest a batch:

```bash
curl -X POST localhost:8000/api/readings -H "Content-Type: application/json" -d '[
  {"device_id": "plc-01", "metric": "temp", "value": 51.4},
  {"device_id": "plc-01", "metric": "pressure", "value": 4.2}
]'
```

## Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./telemetry.db` | any SQLAlchemy URL (swap in Postgres without code changes) |
| `API_KEY` | unset | if set, write requests must send a matching `X-API-Key` header; reads stay open |

## Tests & CI

```bash
pytest -v        # 14 passing
```

Each test runs against its own temporary SQLite database, so the suite is
isolated and deterministic and needs no running server. GitHub Actions runs it
on Python 3.10–3.12.

## License

MIT — see [LICENSE](LICENSE).
