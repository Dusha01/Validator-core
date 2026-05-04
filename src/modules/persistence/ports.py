"""Порты чтения проектов (реализация в sqlalchemy_repository — позже)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from modules.validation.domain.project_row import ProjectRow


@runtime_checkable
class ProjectSourcePort(Protocol):
    def iter_all_projects(self) -> AsyncIterator[ProjectRow]:
        ...
