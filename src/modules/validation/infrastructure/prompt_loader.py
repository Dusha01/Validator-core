from __future__ import annotations
from pathlib import Path
import yaml
from pydantic import ValidationError

from src.modules.validation.infrastructure.prompt_schema import (
    PromptDocument,
    PromptRulesBundle,
    RulesDocument,
)


class PromptLoadError(RuntimeError):
    pass


def _load_yaml_mapping(path: Path, label: str) -> dict:
    if not path.is_file():
        raise PromptLoadError(f"{label} file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise PromptLoadError(f"Invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise PromptLoadError(f"YAML root in {path} must be a mapping")
    return data


def load_prompt_document(path: Path) -> PromptDocument:
    data = _load_yaml_mapping(path, "Prompt")
    try:
        return PromptDocument.model_validate(data)
    except ValidationError as e:
        raise PromptLoadError(f"Invalid prompt document ({path}): {e}") from e


def load_rules_document(path: Path) -> RulesDocument:
    data = _load_yaml_mapping(path, "Rules")
    try:
        return RulesDocument.model_validate(data)
    except ValidationError as e:
        raise PromptLoadError(f"Invalid rules document ({path}): {e}") from e


def load_prompt_rules_bundle(prompt_path: Path, rules_path: Path) -> PromptRulesBundle:
    return PromptRulesBundle(
        prompt=load_prompt_document(prompt_path),
        rules=load_rules_document(rules_path),
    )
