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

    def run(self, model: ModelBase) -> None:
        """Runs the evaluation and prints the metric in the expected format."""
        metric = self.evaluate(model)
        print("---")
        print(f"metric: {metric:.4f}")
