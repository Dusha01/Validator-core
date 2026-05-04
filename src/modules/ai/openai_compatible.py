from __future__ import annotations
import asyncio
import json
from typing import Any
from urllib.parse import urlsplit
import httpx

from src.core.settings import Settings
from src.modules.validation.domain.validation_result import SingleProjectVerdict


class LlmHttpError(RuntimeError):
    pass


# OpenAI strict json_schema: все поля в required, без default-only опущенных ключей.
_STRICT_VERDICT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["ok", "block", "warning", "info"]},
        "summary": {"type": "string"},
        "reason_codes": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["outcome", "summary", "reason_codes"],
    "additionalProperties": False,
}


class OpenAiCompatibleClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm_lock = asyncio.Lock()
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url.rstrip("/"),
            timeout=httpx.Timeout(settings.llm_request_timeout_seconds),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _request_path(self) -> str:
        raw_path = (self._settings.llm_chat_completions_path or "").strip()
        if raw_path.startswith(("http://", "https://")):
            return raw_path

        # Keep a relative path so httpx appends it to base_url path.
        # This avoids losing prefixes like /api/v1 for OpenRouter.
        relative_path = raw_path.lstrip("/")
        if not relative_path:
            relative_path = "chat/completions"

        base_path = urlsplit(self._settings.llm_base_url).path.strip("/")
        if base_path:
            base_parts = base_path.split("/")
            rel_parts = relative_path.split("/")

            # Remove duplicated prefix when path already includes base path.
            if rel_parts[: len(base_parts)] == base_parts:
                rel_parts = rel_parts[len(base_parts) :]

            # Also collapse duplicated API version fragment: /api/v1 + /v1/...
            if base_parts and base_parts[-1] == "v1" and rel_parts and rel_parts[0] == "v1":
                rel_parts = rel_parts[1:]

            relative_path = "/".join(part for part in rel_parts if part)
            if not relative_path:
                relative_path = "chat/completions"

        return relative_path

    async def classify_one(self, *, system: str, user: str) -> SingleProjectVerdict:
        if not (self._settings.llm_api_key or "").strip():
            raise LlmHttpError("LLM_API_KEY is not set")

        path = self._request_path()
        headers = {
            "Authorization": f"Bearer {self._settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        body: dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }

        if self._settings.llm_strict_json_schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "single_project_verdict",
                    "strict": True,
                    "schema": _STRICT_VERDICT_SCHEMA,
                },
            }
        else:
            body["response_format"] = {"type": "json_object"}

        async with self._llm_lock:
            resp = await self._client.post(path, json=body, headers=headers)

        if resp.status_code >= 400:
            raise LlmHttpError(f"LLM HTTP {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LlmHttpError(f"Unexpected LLM response shape: {data!r}") from e

        if not isinstance(content, str):
            raise LlmHttpError(f"LLM content is not a string: {type(content)}")

        content = content.strip()
        try:
            return SingleProjectVerdict.model_validate_json(content)
        except Exception as e:
            if self._settings.llm_strict_json_schema:
                return await self._retry_without_strict(system, user, path, headers)
            raise LlmHttpError(f"Invalid verdict JSON: {content[:300]}") from e

    async def _retry_without_strict(
        self,
        system: str,
        user: str,
        path: str,
        headers: dict[str, str],
    ) -> SingleProjectVerdict:
        body = {
            "model": self._settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        async with self._llm_lock:
            resp = await self._client.post(path, json=body, headers=headers)
        if resp.status_code >= 400:
            raise LlmHttpError(f"LLM HTTP {resp.status_code} (retry): {resp.text[:500]}")
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise LlmHttpError("LLM retry content is not a string")
        return SingleProjectVerdict.model_validate(json.loads(content))
