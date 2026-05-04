from __future__ import annotations
from contextlib import asynccontextmanager
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from fastapi import FastAPI

from src.api.routes import health, reports
from src.core.database import dispose_engine
from src.core.settings import get_settings


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
        description="Валидация проектов через LLM",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(health.router, tags=["health"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    return app


app = create_app()


def _ensure_project_root_on_path() -> None:
    root = Path(__file__).resolve().parent.parent.parent
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def main() -> None:
    _ensure_project_root_on_path()

    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.core.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
