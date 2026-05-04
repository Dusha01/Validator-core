"""Use-case полного прогона валидации (реализация позже)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.settings import Settings


async def run_full_validation(_settings: Settings, trigger: str = "manual") -> str:
    """Вернуть report_id после завершения (заглушка)."""
    raise NotImplementedError("run_full_validation")
