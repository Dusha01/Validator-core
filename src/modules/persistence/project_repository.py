from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import column, select, table
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import Settings
from src.modules.validation.domain.project_row import ProjectRow


def _json_sanitize(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return f"<bytes length={len(value)}>"
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_sanitize(v) for v in value]
    return value


async def fetch_all_project_rows(session: AsyncSession, settings: Settings) -> list[ProjectRow]:
    id_col = settings.projects_id_column
    payload_cols = settings.projects_payload_columns_list
    cols = [column(id_col)] + [column(c) for c in payload_cols]
    t = table(settings.projects_table, *cols, schema=settings.db_schema)
    stmt = select(t)
    result = await session.execute(stmt)
    out: list[ProjectRow] = []
    for row in result.mappings().all():
        raw_id = row[id_col]
        pid = str(raw_id) if raw_id is not None else ""
        payload: dict[str, Any] = {}
        for c in payload_cols:
            payload[c] = _json_sanitize(row[c])
        out.append(ProjectRow(id=pid, payload=payload))
    return out
