"""
Autoresearch MNIST training script.
The agent edits this file freely — architecture, optimizer, hyperparameters.
Usage: uv run train_mnist.py
"""

import time
import torch
import torch.nn as nn
import torch.nn.functional as F
from prep_mnist import TIME_BUDGET, get_device, get_dataloaders, evaluate_accuracy

# ---------------------------------------------------------------------------
# Hyperparameters (edit these directly)
# ---------------------------------------------------------------------------

HIDDEN_DIM = 128
N_LAYERS = 1               # number of hidden layers
ACTIVATION = "relu"        # relu, gelu, silu
DROPOUT = 0.0
BATCH_NORM = False

LEARNING_RATE = 0.001
BATCH_SIZE = 64
OPTIMIZER = "adam"         # adam, sgd
WEIGHT_DECAY = 0.0
MOMENTUM = 0.9             # only for SGD

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

def get_activation(name):
    if name == "relu":
        return nn.ReLU()
    elif name == "gelu":
        return nn.GELU()
    elif name == "silu":
        return nn.SiLU()
    else:
        raise ValueError(f"Unknown activation: {name}")

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        layers = []
        in_dim = 784
        for i in range(N_LAYERS):
            layers.append(nn.Linear(in_dim, HIDDEN_DIM))
            if BATCH_NORM:
                layers.append(nn.BatchNorm1d(HIDDEN_DIM))
            layers.append(get_activation(ACTIVATION))
            if DROPOUT > 0:
                layers.append(nn.Dropout(DROPOUT))
            in_dim = HIDDEN_DIM
        layers.append(nn.Linear(in_dim, 10))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.net(x)

# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

def get_optimizer(model):
    if OPTIMIZER == "adam":
        return torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    elif OPTIMIZER == "sgd":
        return torch.optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
    else:
        raise ValueError(f"Unknown optimizer: {OPTIMIZER}")

# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def main():
    t_start = time.time()
    device = get_device()
    print(f"Device: {device}")

    train_loader, val_loader = get_dataloaders(BATCH_SIZE)

    model = Model().to(device)
    num_params = sum(p.numel() for p in model.parameters())
    print(f"Parameters: {num_params:,}")

    optimizer = get_optimizer(model)
    criterion = nn.CrossEntropyLoss()

    t_start_train = time.time()
    step = 0
    smooth_loss = 0.0

    while True:
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)

            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            step += 1
            loss_f = loss.item()

            # Fast fail: NaN or exploding loss
            if torch.isnan(loss) or loss_f > 100:
                print("FAIL: NaN or exploding loss")
                exit(1)

            smooth_loss = 0.9 * smooth_loss + 0.1 * loss_f if smooth_loss else loss_f

            if step % 100 == 0:
                elapsed = time.time() - t_start_train
                pct = 100 * elapsed / TIME_BUDGET
                print(f"\rstep {step:05d} ({pct:.0f}%) | loss: {smooth_loss:.4f} | elapsed: {elapsed:.0f}s    ", end="", flush=True)

            elapsed = time.time() - t_start_train
            if elapsed >= TIME_BUDGET:
                break

        elapsed = time.time() - t_start_train
        if elapsed >= TIME_BUDGET:
            break

    training_time = time.time() - t_start_train
    print()

    # Final eval
    model.eval()
    val_acc = evaluate_accuracy(model, val_loader, device)

    t_end = time.time()

    if device.type == "cuda":
        peak_memory_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
    elif device.type == "mps":
        peak_memory_mb = torch.mps.current_allocated_memory() / 1024 / 1024 if hasattr(torch.mps, 'current_allocated_memory') else 0.0
    else:
        peak_memory_mb = 0.0

    print("---")
    print(f"val_accuracy: {val_acc:.4f}")
    print(f"training_seconds: {training_time:.1f}")
    print(f"total_seconds: {t_end - t_start:.1f}")
    print(f"peak_memory_mb: {peak_memory_mb:.1f}")
    print(f"num_params: {num_params}")
    print(f"num_steps: {step}")

if __name__ == "__main__":
    main()
