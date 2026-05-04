"""Строка проекта из БД — вход в валидатор."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectRow(BaseModel):
    """Идентификатор + полезная нагрузка колонок из PROJECTS_PAYLOAD_COLUMNS."""

    id: str
    payload: dict[str, Any] = Field(default_factory=dict)
