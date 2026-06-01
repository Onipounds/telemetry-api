"""FastAPI application: thin web layer over the CRUD functions.

    uvicorn telemetry_api.app:app --reload

Endpoints
    GET  /health
    POST /api/readings                 ingest a batch of readings (auth)
    GET  /api/readings                 query with filters
    GET  /api/devices                  list known device ids
    GET  /api/devices/{id}/latest      latest reading per metric for a device
    GET  /api/stats                    aggregate stats for a device + metric
"""

from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from . import crud
from .config import get_settings
from .db import get_session, init_engine
from .schemas import IngestResult, ReadingIn, ReadingOut, Stats


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require a valid X-API-Key only when an API_KEY is configured."""
    expected = get_settings().api_key
    if expected is None:
        return  # auth disabled (dev/test)
    if x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing API key"
        )


def create_app() -> FastAPI:
    init_engine()
    app = FastAPI(title="Telemetry API", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/readings", response_model=IngestResult,
              status_code=status.HTTP_201_CREATED,
              dependencies=[Depends(require_api_key)])
    def ingest(readings: list[ReadingIn], session: Session = Depends(get_session)) -> IngestResult:
        if not readings:
            raise HTTPException(status_code=422, detail="empty batch")
        n = crud.insert_readings(session, readings)
        return IngestResult(ingested=n)

    @app.get("/api/readings", response_model=list[ReadingOut])
    def read(
        session: Session = Depends(get_session),
        device_id: str | None = None,
        metric: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = Query(default=100, ge=1, le=10_000),
    ) -> list[ReadingOut]:
        rows = crud.query_readings(session, device_id, metric, since, until, limit)
        return [ReadingOut.model_validate(r) for r in rows]

    @app.get("/api/devices", response_model=list[str])
    def devices(session: Session = Depends(get_session)) -> list[str]:
        return crud.list_devices(session)

    @app.get("/api/devices/{device_id}/latest", response_model=list[ReadingOut])
    def latest(device_id: str, session: Session = Depends(get_session)) -> list[ReadingOut]:
        rows = crud.latest_per_metric(session, device_id)
        return [ReadingOut.model_validate(r) for r in rows]

    @app.get("/api/stats", response_model=Stats)
    def stats(
        device_id: str,
        metric: str,
        session: Session = Depends(get_session),
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> Stats:
        return crud.compute_stats(session, device_id, metric, since, until)

    @app.get("/api/alerts", response_model=list[ReadingOut])
    def alerts(
        threshold: float,
        session: Session = Depends(get_session),
        metric: str | None = None,
        limit: int = Query(default=100, ge=1, le=10_000),
    ) -> list[ReadingOut]:
        rows = crud.readings_over_limit(session, threshold, metric, limit)
        return [ReadingOut.model_validate(r) for r in rows]

    return app


app = create_app()