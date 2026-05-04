from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    db_host: str = Field(default="localhost", validation_alias="DB_HOST")
    db_port: int = Field(default=5432, validation_alias="DB_PORT")
    db_user: str = Field(default="postgres", validation_alias="DB_USER")
    db_password: str = Field(default="postgres", validation_alias="DB_PASSWORD")
    db_name: str = Field(default="app", validation_alias="DB_NAME")
    db_schema: str = Field(default="public", validation_alias="DB_SCHEMA")

    projects_table: str = Field(default="projects", validation_alias="PROJECTS_TABLE")
    projects_id_column: str = Field(default="id", validation_alias="PROJECTS_ID_COLUMN")
    projects_payload_columns_raw: str = Field(
        default="name,description",
        validation_alias="PROJECTS_PAYLOAD_COLUMNS",
    )

    # --- Scheduler ---
    validation_cron: str | None = Field(default=None, validation_alias="VALIDATION_CRON")
    validation_interval_seconds: int = Field(
        default=3600,
        ge=60,
        validation_alias="VALIDATION_INTERVAL_SECONDS",
    )

    validation_chunk_size: int = Field(default=20, ge=1, le=500, validation_alias="VALIDATION_CHUNK_SIZE")

    # --- LLM ---
    llm_base_url: str = Field(default="https://api.openai.com", validation_alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")
    llm_chat_completions_path: str = Field(
        default="/v1/chat/completions",
        validation_alias="LLM_CHAT_COMPLETIONS_PATH",
    )
    llm_request_timeout_seconds: float = Field(
        default=120.0,
        ge=5.0,
        validation_alias="LLM_REQUEST_TIMEOUT_SECONDS",
    )
    llm_strict_json_schema: bool = Field(default=True, validation_alias="LLM_STRICT_JSON_SCHEMA")

    # --- Paths ---
    reports_dir: Path | None = Field(default=None, validation_alias="REPORTS_DIR")
    public_prompt_file: Path | None = Field(default=None, validation_alias="PUBLIC_PROMPT_FILE")
    public_rules_file: Path | None = Field(default=None, validation_alias="PUBLIC_RULES_FILE")

    # --- API ---
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, ge=1, le=65535, validation_alias="API_PORT")
    admin_api_key: str | None = Field(default=None, validation_alias="ADMIN_API_KEY")

    @field_validator("public_prompt_file", "public_rules_file", mode="before")
    @classmethod
    def _empty_path_override_to_none(cls, v: object) -> Path | None:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v  # type: ignore[return-value]

    @field_validator("admin_api_key", mode="before")
    @classmethod
    def _empty_admin_key_to_none(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        raise TypeError("ADMIN_API_KEY must be a string or null")

    @field_validator(
        "db_schema",
        "projects_table",
        "projects_id_column",
        mode="before",
    )
    @classmethod
    def _validate_sql_identifiers(cls, v: str) -> str:
        if not isinstance(v, str) or not _IDENTIFIER_RE.match(v):
            raise ValueError(f"Invalid SQL identifier: {v!r}")
        return v

    @field_validator("projects_payload_columns_raw", mode="before")
    @classmethod
    def _normalize_payload_columns(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        raise TypeError("PROJECTS_PAYLOAD_COLUMNS must be a string")

    @model_validator(mode="after")
    def _validate_payload_column_names(self) -> Settings:
        cols = self.projects_payload_columns_list
        if not cols:
            raise ValueError("PROJECTS_PAYLOAD_COLUMNS must list at least one column")
        for c in cols:
            if not _IDENTIFIER_RE.match(c):
                raise ValueError(f"Invalid payload column name: {c!r}")
        if self.projects_id_column in cols:
            raise ValueError("PROJECTS_ID_COLUMN must not appear in PROJECTS_PAYLOAD_COLUMNS")
        return self

    @computed_field
    @property
    def project_root(self) -> Path:
        return _project_root()

    @computed_field
    @property
    def reports_path(self) -> Path:
        if self.reports_dir is not None:
            return Path(self.reports_dir).expanduser().resolve()
        return self.project_root / "reports"

    @computed_field
    @property
    def prompt_file_path(self) -> Path:
        if self.public_prompt_file is not None:
            return Path(self.public_prompt_file).expanduser().resolve()
        return self.project_root / "public" / "promt.yml"

    @computed_field
    @property
    def rules_file_path(self) -> Path:
        if self.public_rules_file is not None:
            return Path(self.public_rules_file).expanduser().resolve()
        return self.project_root / "public" / "rules.yml"

    @computed_field
    @property
    def projects_payload_columns_list(self) -> list[str]:
        parts = [p.strip() for p in self.projects_payload_columns_raw.split(",")]
        return [p for p in parts if p]

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
