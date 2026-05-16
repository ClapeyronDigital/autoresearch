import os
import time
import torch
import torch.nn as nn
import torchvision
import torchvision.transforms as T
from workdir.model import Model, get_activation
from eval.evaluate import evaluate, CACHE_DIR, TRANSFORM

# ---------------------------------------------------------------------------
# Hyperparameters (agent edits these)
# ---------------------------------------------------------------------------

LEARNING_RATE = 0.001
BATCH_SIZE = 64
OPTIMIZER = "adam"
WEIGHT_DECAY = 0.0
MOMENTUM = 0.9
TIME_BUDGET = 60


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def get_train_loader(batch_size):
    os.makedirs(CACHE_DIR, exist_ok=True)
    train_dataset = torchvision.datasets.MNIST(
        root=CACHE_DIR, train=True, download=True, transform=TRANSFORM,
    )
    return torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=0, pin_memory=False,
    )


def get_optimizer(model):
    if OPTIMIZER == "adam":
        return torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    elif OPTIMIZER == "sgd":
        return torch.optim.SGD(model.parameters(), lr=LEARNING_RATE, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
    raise ValueError(f"Unknown optimizer: {OPTIMIZER}")


def main():
    t_start = time.time()
    device = get_device()

    train_loader = get_train_loader(BATCH_SIZE)

    model = Model().to(device)
    num_params = sum(p.numel() for p in model.parameters())

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

    metric = evaluate(model)

    t_end = time.time()

    if device.type == "cuda":
        peak_memory_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
    elif device.type == "mps":
        peak_memory_mb = torch.mps.current_allocated_memory() / 1024 / 1024 if hasattr(torch.mps, 'current_allocated_memory') else 0.0
    else:
        peak_memory_mb = 0.0

    print("---")
    print(f"metric: {metric:.4f}")
    print(f"training_seconds: {training_time:.1f}")
    print(f"total_seconds: {t_end - t_start:.1f}")
    print(f"peak_memory_mb: {peak_memory_mb:.1f}")
    print(f"num_params: {num_params}")
    print(f"num_steps: {step}")


if __name__ == "__main__":
    main()
