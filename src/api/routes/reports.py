from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import SettingsDep, require_admin_key

router = APIRouter()


@router.get("/", summary="Список отчётов валидации")
async def list_reports(_settings: SettingsDep) -> dict:
    # TODO: modules.reports — чтение каталога / индекса
    return {"items": []}


@router.post(
    "/run",
    summary="Принудительный запуск валидации",
    dependencies=[Depends(require_admin_key)],
)
async def run_validation(_settings: SettingsDep) -> dict:
    # TODO: use-case RunValidation + фон / lock
    return {"status": "accepted", "detail": "not implemented"}


@router.get("/{report_id}", summary="Получить отчёт по id")
async def get_report(report_id: str, _settings: SettingsDep) -> dict:
    # TODO: загрузка JSON из reports/{report_id}.json
    return {"id": report_id, "detail": "not implemented"}


@router.delete(
    "/{report_id}",
    summary="Удалить отчёт",
    dependencies=[Depends(require_admin_key)],
)
async def delete_report(report_id: str, _settings: SettingsDep) -> dict:
    # TODO: удаление файла отчёта
    return {"deleted": False, "id": report_id, "detail": "not implemented"}
