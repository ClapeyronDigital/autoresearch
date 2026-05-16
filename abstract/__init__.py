from abc import ABC, abstractmethod
from typing import Any


class ModelBase(ABC):
    """Agent inherits this class in workdir/model.py."""

    @abstractmethod
    def predict(self, x: Any) -> Any: ...


class EvaluatorBase(ABC):
    """User inherits this class in eval/evaluate.py."""

    @abstractmethod
    def evaluate(self, model: ModelBase) -> float: ...
