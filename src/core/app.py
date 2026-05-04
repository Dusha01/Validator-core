"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI

from api.routes import health, reports
from core.database import dispose_engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@asynccontextmanager
async def lifespan(_app: FastAPI) -> "AsyncIterator[None]":
    # TODO: start APScheduler for periodic validation
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Validator-core",
        description="Валидация проектов через LLM и отчёты для админки",
        lifespan=lifespan,
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    return app


app = create_app()
