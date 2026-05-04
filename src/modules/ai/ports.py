"""Порт вызова LLM."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LlmClientPort(Protocol):
    async def complete_json(self, *, system: str, user: str, json_schema: dict) -> str:
        """Вернуть сырое JSON-тело ответа ассистента."""
        ...
