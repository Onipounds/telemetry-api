"""Data-access layer: all database queries live here, separate from the API.

Keeping these out of the route handlers makes them unit-testable on their own
and keeps the web layer thin.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Reading
from .schemas import ReadingIn, Stats


def _aware_to_naive_utc(dt: datetime | None) -> datetime | None:
    """Store/compare everything as naive UTC for SQLite consistency."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def insert_readings(session: Session, readings: list[ReadingIn]) -> int:
    objs = []
    for r in readings:
        ts = _aware_to_naive_utc(r.ts) or datetime.now(timezone.utc).replace(tzinfo=None)
        objs.append(Reading(device_id=r.device_id, metric=r.metric, value=r.value, ts=ts))
    session.add_all(objs)
    session.commit()
    return len(objs)


def query_readings(
    session: Session,
    device_id: str | None = None,
    metric: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 100,
) -> list[Reading]:
    stmt = select(Reading)
    if device_id:
        stmt = stmt.where(Reading.device_id == device_id)
    if metric:
        stmt = stmt.where(Reading.metric == metric)
    if since:
        stmt = stmt.where(Reading.ts >= _aware_to_naive_utc(since))
    if until:
        stmt = stmt.where(Reading.ts <= _aware_to_naive_utc(until))
    stmt = stmt.order_by(Reading.ts.desc()).limit(limit)
    return list(session.scalars(stmt))


def list_devices(session: Session) -> list[str]:
    stmt = select(Reading.device_id).distinct().order_by(Reading.device_id)
    return list(session.scalars(stmt))


def latest_per_metric(session: Session, device_id: str) -> list[Reading]:
    """Most recent reading for each metric reported by a device."""
    # find the max ts per metric, then fetch those rows
    sub = (
        select(Reading.metric, func.max(Reading.ts).label("max_ts"))
        .where(Reading.device_id == device_id)
        .group_by(Reading.metric)
        .subquery()
    )
    stmt = select(Reading).join(
        sub,
        (Reading.metric == sub.c.metric)
        & (Reading.ts == sub.c.max_ts)
        & (Reading.device_id == device_id),
    )
    return list(session.scalars(stmt))


def compute_stats(
    session: Session,
    device_id: str,
    metric: str,
    since: datetime | None = None,
    until: datetime | None = None,
) -> Stats:
    stmt = select(
        func.count(Reading.value),
        func.min(Reading.value),
        func.max(Reading.value),
        func.avg(Reading.value),
        func.min(Reading.ts),
        func.max(Reading.ts),
    ).where(Reading.device_id == device_id, Reading.metric == metric)
    if since:
        stmt = stmt.where(Reading.ts >= _aware_to_naive_utc(since))
    if until:
        stmt = stmt.where(Reading.ts <= _aware_to_naive_utc(until))

    count, mn, mx, avg, first_ts, last_ts = session.execute(stmt).one()
    return Stats(
        device_id=device_id,
        metric=metric,
        count=count or 0,
        min=mn,
        max=mx,
        avg=round(avg, 6) if avg is not None else None,
        first_ts=first_ts,
        last_ts=last_ts,
    )
def readings_over_limit(
    session: Session,
    threshold: float,
    metric: str | None = None,
    limit: int = 100,
) -> list[Reading]:
    """Alert query: readings whose value exceeds a threshold.

    Demonstrates a filtered SELECT with a comparison on the value column,
    ordered worst-first.
    """
    stmt = select(Reading).where(Reading.value > threshold)
    if metric:
        stmt = stmt.where(Reading.metric == metric)
    stmt = stmt.order_by(Reading.value.desc()).limit(limit)
    return list(session.scalars(stmt))