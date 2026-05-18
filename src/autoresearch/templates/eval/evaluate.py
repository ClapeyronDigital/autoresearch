from abstract import EvaluatorBase, ModelBase


class Evaluator(EvaluatorBase):
    def evaluate(self, model: ModelBase) -> float:
        print("[WARN] You are using a stub Evaluator. Implement evaluate() for your project.")
        return 0.0


if __name__ == "__main__":
    from workdir.model import Model

    evaluator = Evaluator()
    model = Model()
    evaluator.run(model)
