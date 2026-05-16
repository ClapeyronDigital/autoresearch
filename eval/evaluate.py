import os
import torch
import torchvision
import torchvision.transforms as T

from abstract import EvaluatorBase, ModelBase

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "autoresearch-mnist")

TRANSFORM = T.Compose([
    T.ToTensor(),
    T.Normalize((0.1307,), (0.3081,)),
])


class MyEvaluator(EvaluatorBase):
    def __init__(self):
        self.device = self._get_device()
        self.val_loader = self._get_val_loader()
        os.makedirs(CACHE_DIR, exist_ok=True)

    @staticmethod
    def _get_device():
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    @staticmethod
    def _get_val_loader():
        val_dataset = torchvision.datasets.MNIST(
            root=CACHE_DIR, train=False, download=True, transform=TRANSFORM,
        )
        return torch.utils.data.DataLoader(
            val_dataset, batch_size=1024, shuffle=False,
            num_workers=0, pin_memory=False,
        )

    @torch.no_grad()
    def evaluate(self, model: ModelBase) -> float:
        if hasattr(model, 'to'):
            model.to(self.device)
        if hasattr(model, 'eval'):
            model.eval()

        correct = 0
        total = 0
        for x, y in self.val_loader:
            x, y = x.to(self.device), y.to(self.device)
            logits = model.predict(x)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += y.size(0)
        return correct / total if total > 0 else 0.0


evaluate = MyEvaluator().evaluate
