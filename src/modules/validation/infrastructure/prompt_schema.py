from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ValidationRule(BaseModel):
    id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    criterion: str = Field(..., min_length=1)
    severity: str | None = Field(
        default=None,
        description="info | warning | block — опционально для приоритизации",
    )

    @field_validator("severity")
    @classmethod
    def _normalize_severity(cls, v: str | None) -> str | None:
        if v is None:
            return None
        allowed = {"info", "warning", "block"}
        low = v.strip().lower()
        if low not in allowed:
            raise ValueError(f"severity must be one of {allowed}, got {v!r}")
        return low


class PromptDocument(BaseModel):
    version: int = 1
    system_prompt: str = Field(..., min_length=1)


class RulesDocument(BaseModel):
    version: int = 1
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    output_contract: str = Field(
        default="",
        description="Текстовое напоминание формата JSON для модели",
    )


class PromptRulesBundle(BaseModel):
    prompt: PromptDocument
    rules: RulesDocument
