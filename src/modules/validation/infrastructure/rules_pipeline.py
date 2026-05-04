from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Sequence
import yaml

from src.modules.validation.infrastructure.prompt_schema import (
    PromptRulesBundle,
    ValidationRule,
)


class BaseRule(ABC):
    @abstractmethod
    def serialize(self, rule: ValidationRule) -> dict[str, Any]:
        """Serialize one rule to a AML-friendly mapping."""


class DefaultRule(BaseRule):
    def serialize(self, rule: ValidationRule) -> dict[str, Any]:
        return rule.model_dump(exclude_none=True)


class BaseLayer(ABC):
    @abstractmethod
    def render(self, bundle: PromptRulesBundle) -> str:
        """Render one section of the final prompt."""


class SystemPromptLayer(BaseLayer):
    def render(self, bundle: PromptRulesBundle) -> str:
        return bundle.prompt.system_prompt.strip()


class ValidationRulesLayer(BaseLayer):
    def __init__(
        self,
        *,
        title: str = "Validation rules (YAML):",
        serializer: BaseRule | None = None,
    ) -> None:
        self._title = title
        self._serializer = serializer or DefaultRule()

    def render(self, bundle: PromptRulesBundle) -> str:
        rules_yaml = yaml.safe_dump(
            {
                "validation_rules": [
                    self._serializer.serialize(rule)
                    for rule in bundle.rules.validation_rules
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ).strip()
        return f"{self._title}\n{rules_yaml}"


class OutputContractLayer(BaseLayer):
    def __init__(self, *, title: str = "Single-response contract (output_contract):") -> None:
        self._title = title

    def render(self, bundle: PromptRulesBundle) -> str:
        return f"{self._title}\n{bundle.rules.output_contract.strip()}"


class RulesPipeline:
    def __init__(self, layers: Sequence[BaseLayer]) -> None:
        self._layers = list(layers)

    @classmethod
    def default(cls) -> "RulesPipeline":
        return cls(
            [
                SystemPromptLayer(),
                ValidationRulesLayer(),
                OutputContractLayer(),
            ]
        )

    def build(self, bundle: PromptRulesBundle) -> str:
        return "\n\n".join(
            chunk for chunk in (layer.render(bundle).strip() for layer in self._layers) if chunk
        )
