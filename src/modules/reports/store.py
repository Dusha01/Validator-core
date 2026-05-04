from __future__ import annotations
import re
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.core.settings import Settings


_SAFE_REPORT_ID = re.compile(
    r"^project-inspect-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{3}Z$",
)


def validate_report_id(report_id: str) -> str:
    if not isinstance(report_id, str):
        raise TypeError("report_id must be a string")
    normalized = report_id.strip()
    if not _SAFE_REPORT_ID.match(normalized):
        raise ValueError(
            "report_id must match project-inspect-YYYY-MM-DDTHH-MM-SS.mmmZ"
        )
    return normalized


def reports_directory(settings: Settings) -> Path:
    path = settings.reports_path
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_file_path(settings: Settings, report_id: str) -> Path:
    return reports_directory(settings) / f"{validate_report_id(report_id)}.json"
