"""Точка входа: запуск uvicorn с PYTHONPATH=src."""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root = Path(__file__).resolve().parent
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> None:
    _ensure_src_on_path()
    import uvicorn

    from core.settings import get_settings

    settings = get_settings()
    uvicorn.run(
        "core.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
