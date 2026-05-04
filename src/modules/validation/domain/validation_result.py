from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class SingleProjectVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: Literal["ok", "block", "warning", "info"]
    summary: str = ""
    reason_codes: list[str] = Field(default_factory=list)


class FlaggedProject(BaseModel):
    project_id: str
    summary: str = ""
    reason_codes: list[str] = Field(default_factory=list)


class ProcessingError(BaseModel):
    project_id: str
    error: str


class SavedModerationReport(BaseModel):
    id: str
    created_at: str
    trigger: str
    block: list[FlaggedProject] = Field(default_factory=list)
    warning: list[FlaggedProject] = Field(default_factory=list)
    info: list[FlaggedProject] = Field(default_factory=list)
    processing_errors: list[ProcessingError] = Field(default_factory=list)
