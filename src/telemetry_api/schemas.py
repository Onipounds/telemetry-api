"""Pydantic schemas for request validation and response shaping."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReadingIn(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    metric: str = Field(min_length=1, max_length=128)
    value: float
    ts: datetime | None = None      # server fills with UTC now if omitted


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    metric: str
    value: float
    ts: datetime


class IngestResult(BaseModel):
    ingested: int


class Stats(BaseModel):
    device_id: str
    metric: str
    count: int
    min: float | None = None
    max: float | None = None
    avg: float | None = None
    first_ts: datetime | None = None
    last_ts: datetime | None = None
