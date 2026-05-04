"""Structured output от LLM (контракт ответа)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class JudgedProject(BaseModel):
    project_id: str
    summary: str = ""
    reason_codes: list[str] = Field(default_factory=list)


class ValidationResultMeta(BaseModel):
    run_note: str | None = None


class ValidationResultPayload(BaseModel):
    """Тело ответа модели после парсинга JSON."""

    valid: list[JudgedProject] = Field(default_factory=list)
    invalid: list[JudgedProject] = Field(default_factory=list)
    disputed: list[JudgedProject] = Field(default_factory=list)
    meta: ValidationResultMeta | None = None


class SavedValidationReport(BaseModel):
    """Файл отчёта на диске: обёртка над результатом + служебные поля."""

    id: str
    created_at: str
    trigger: str  # scheduled | manual
    result: ValidationResultPayload
