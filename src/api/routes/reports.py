from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.deps import SettingsDep, require_admin_key
from src.modules.reports.report_storage import (
    delete_moderation_report,
    list_report_summaries,
    load_moderation_report,
)
from src.modules.validation.application.run_validation import (
    run_full_validation,
    validation_run_lock,
)

router = APIRouter()


@router.get("/", summary="Список отчётов валидации")
async def list_reports(settings: SettingsDep) -> dict:
    return {"items": list_report_summaries(settings)}


@router.post(
    "/run",
    summary="Принудительный запуск валидации",
    dependencies=[Depends(require_admin_key)],
)
async def run_validation(settings: SettingsDep) -> dict:
    async with validation_run_lock:
        try:
            report_id = await run_full_validation(settings, trigger="manual")
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)[:2000],
            ) from e
    return {"status": "done", "report_id": report_id}


@router.get("/{report_id}", summary="Получить отчёт по id")
async def get_report(report_id: str, settings: SettingsDep) -> dict:
    try:
        report = load_moderation_report(settings, report_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found") from None
    return report.model_dump(mode="json")


@router.delete(
    "/{report_id}",
    summary="Удалить отчёт",
    dependencies=[Depends(require_admin_key)],
)
async def delete_report(report_id: str, settings: SettingsDep) -> dict:
    try:
        deleted = delete_moderation_report(settings, report_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {"deleted": True, "id": report_id}
