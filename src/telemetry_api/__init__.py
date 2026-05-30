"""telemetry_api: a small FastAPI service for ingesting and querying sensor telemetry."""

from .app import create_app

__all__ = ["create_app"]
__version__ = "0.1.0"
