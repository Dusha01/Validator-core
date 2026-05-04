from __future__ import annotations
import json
from pathlib import Path

from src.core.settings import Settings
from src.modules.reports.store import report_file_path, reports_directory, validate_report_id
from src.modules.validation.domain.validation_result import SavedModerationReport


def _parse_report_id(report_id: str) -> str:
    return validate_report_id(report_id)


def save_moderation_report(settings: Settings, report: SavedModerationReport) -> Path:
    _parse_report_id(report.id)
    path = report_file_path(settings, report.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = report.model_dump(mode="json")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_moderation_report(settings: Settings, report_id: str) -> SavedModerationReport:
    rid = _parse_report_id(report_id)
    path = report_file_path(settings, rid)
    if not path.is_file():
        raise FileNotFoundError(rid)
    return SavedModerationReport.model_validate_json(path.read_text(encoding="utf-8"))


def delete_moderation_report(settings: Settings, report_id: str) -> bool:
    rid = _parse_report_id(report_id)
    path = report_file_path(settings, rid)
    if not path.is_file():
        return False
    path.unlink()
    return True


def list_report_summaries(settings: Settings) -> list[dict]:
    root = reports_directory(settings)
    items: list[dict] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_report_id(str(data.get("id", "")))
        except (ValueError, json.JSONDecodeError, TypeError):
            continue
        items.append(
            {
                "id": data.get("id"),
                "created_at": data.get("created_at"),
                "trigger": data.get("trigger"),
                "counts": {
                    "block": len(data.get("block") or []),
                    "warning": len(data.get("warning") or []),
                    "info": len(data.get("info") or []),
                    "processing_errors": len(data.get("processing_errors") or []),
                },
            }
        )
    return items
