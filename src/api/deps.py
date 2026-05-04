from __future__ import annotations
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status

from src.core.settings import Settings, get_settings


def settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(settings_dep)]


async def require_admin_key(
    settings: SettingsDep,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> None:
    expected = (settings.admin_api_key or "").strip()
    if not expected:
        return
    if (x_admin_key or "").strip() != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key",
        )
