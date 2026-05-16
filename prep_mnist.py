"""
One-time data preparation for MNIST autoresearch.
Downloads MNIST, provides dataloaders and evaluation.

Usage:
    python prep_mnist.py              # download MNIST and verify

Data is cached in ~/.cache/autoresearch-mnist/.
"""

import os
import torch
import torchvision
import torchvision.transforms as T

# ---------------------------------------------------------------------------
# Constants (fixed, do not modify)
# ---------------------------------------------------------------------------

TIME_BUDGET = 60            # training time budget in seconds
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "autoresearch-mnist")

# Standard MNIST normalization
TRANSFORM = T.Compose([
    T.ToTensor(),
    T.Normalize((0.1307,), (0.3081,)),
])

# ---------------------------------------------------------------------------
# Device detection
# ---------------------------------------------------------------------------

def get_device():
    """Auto-detect best available device: CUDA > MPS > CPU."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    else:
        return torch.device("cpu")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def get_dataloaders(batch_size):
    """
    Returns (train_loader, val_loader) for MNIST.
    Train: 60k samples, shuffled. Val: 10k test set, not shuffled.
    Downloads to CACHE_DIR on first call.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    train_dataset = torchvision.datasets.MNIST(
        root=CACHE_DIR, train=True, download=True, transform=TRANSFORM
    )
    val_dataset = torchvision.datasets.MNIST(
        root=CACHE_DIR, train=False, download=True, transform=TRANSFORM
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=0, pin_memory=False,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=False,
    )

    return train_loader, val_loader

# ---------------------------------------------------------------------------
# Evaluation (DO NOT CHANGE — this is the fixed metric)
# ---------------------------------------------------------------------------

@torch.no_grad()
def evaluate_accuracy(model, val_loader, device):
    """Fixed validation metric: classification accuracy on the MNIST test set."""
    correct = 0
    total = 0
    for x, y in val_loader:
        x, y = x.to(device), y.to(device)
        logits = model(x)
        preds = logits.argmax(dim=1)
        correct += (preds == y).sum().item()
        total += y.size(0)
    return correct / total if total > 0 else 0.0

# ---------------------------------------------------------------------------
# Main (for one-time setup / verification)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    device = get_device()
    print(f"Device: {device}")
    print(f"Cache directory: {CACHE_DIR}")
    print()

    print("Downloading MNIST...")
    train_loader, val_loader = get_dataloaders(batch_size=64)
    print(f"Train samples: {len(train_loader.dataset):,}")
    print(f"Val samples:   {len(val_loader.dataset):,}")
    print(f"Train batches: {len(train_loader)}")
    print(f"Val batches:   {len(val_loader)}")
    print()

    print("MNIST data ready. You can now run experiments with:")
    print("  uv run train_mnist.py")
