from __future__ import annotations
import asyncio
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.core.database import session_scope
from src.modules.ai.openai_compatible import LlmHttpError, OpenAiCompatibleClient
from src.modules.persistence.project_repository import fetch_all_project_rows
from src.modules.reports.report_storage import save_moderation_report
from src.modules.validation.domain.validation_result import (
    FlaggedProject,
    ProcessingError,
    SavedModerationReport,
)
from src.modules.validation.infrastructure.prompt_loader import load_prompt_rules_bundle
from src.modules.validation.infrastructure.rules_pipeline import RulesPipeline


if TYPE_CHECKING:
    from src.core.settings import Settings

validation_run_lock = asyncio.Lock()


def _new_report_id(now: datetime | None = None) -> str:
    ts = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H-%M-%S.%f")
    return f"project-inspect-{ts[:-3]}Z"


async def run_full_validation(settings: Settings, trigger: str = "manual") -> str:
    if not (settings.llm_api_key or "").strip():
        raise RuntimeError("LLM_API_KEY is required for validation")

    bundle = load_prompt_rules_bundle(settings.prompt_file_path, settings.rules_file_path)
    system = RulesPipeline.default().build(bundle)

    async with session_scope(settings) as session:
        projects = await fetch_all_project_rows(session, settings)

    report_id = _new_report_id()
    block: list[FlaggedProject] = []
    warning: list[FlaggedProject] = []
    info: list[FlaggedProject] = []
    processing_errors: list[ProcessingError] = []

    client = OpenAiCompatibleClient(settings)
    try:
        for p in projects:
            if not p.id:
                processing_errors.append(
                    ProcessingError(project_id="", error="empty project id, skipped")
                )
                continue
            user = json.dumps(
                {"project_id": p.id, "fields": p.payload},
                ensure_ascii=False,
            )
            try:
                verdict = await client.classify_one(system=system, user=user)
                if verdict.outcome == "ok":
                    continue
                flagged = FlaggedProject(
                    project_id=p.id,
                    summary=verdict.summary,
                    reason_codes=list(verdict.reason_codes),
                )
                if verdict.outcome == "block":
                    block.append(flagged)
                elif verdict.outcome == "warning":
                    warning.append(flagged)
                else:
                    info.append(flagged)
            except (LlmHttpError, ValueError, TypeError, KeyError) as e:
                processing_errors.append(
                    ProcessingError(project_id=p.id, error=str(e)[:2000])
                )
    finally:
        await client.aclose()

    report = SavedModerationReport(
        id=report_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        trigger=trigger,
        block=block,
        warning=warning,
        info=info,
        processing_errors=processing_errors,
    )
    save_moderation_report(settings, report)
    return report_id
