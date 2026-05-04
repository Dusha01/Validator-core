"""Файловое хранилище отчётов (каталог из settings.reports_path)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.settings import Settings


def reports_directory(settings: Settings) -> Path:
    path = settings.reports_path
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_file_path(settings: Settings, report_id: str) -> Path:
    # report_id должен быть безопасным (UUID) — проверка при записи в use-case
    return reports_directory(settings) / f"{report_id}.json"
