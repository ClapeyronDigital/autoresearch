from abstract import EvaluatorBase, ModelBase


class MyEvaluator(EvaluatorBase):
    def evaluate(self, model: ModelBase) -> float:
        # TODO: implement model evaluation
        # Call model.predict() on test data, compute metric.
        # Returns float, higher is better.
        raise NotImplementedError("Implement evaluate() for your project")


evaluate = MyEvaluator().evaluate
