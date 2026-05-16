# Project: MNIST Digit Classification

## Description

Classify handwritten digits from the MNIST dataset. The model takes 28x28
grayscale images and outputs class probabilities for digits 0-9.

## Contract: model ↔ eval

`Model.predict(x)` receives:
  - `x`: torch.Tensor of shape (B, 1, 28, 28), values after ToTensor+Normalize

Returns:
  - torch.Tensor of shape (B, 10) — raw logits per class (0-9)

`evaluate(model)` calls `model.predict()` on the MNIST test set (10k samples),
computes classification accuracy, and returns a float in [0, 1].

The model must handle its own device placement — `evaluate()` will call
`model.to(device)` and `model.eval()` if the methods exist.

## Baseline

- Baseline metric: ~0.977 (simple MLP, 128 hidden, ReLU, Adam, 60s training)
- Baseline model: MLP with configurable width/depth/activation/dropout in
  `workdir/model.py`. Training loop in `workdir/train.py`.

## How to run

```
python workdir/train.py
```

This trains the model for `TIME_BUDGET` seconds, then calls `evaluate()`.

## Agent instructions

The agent edits everything in `workdir/`. To run an experiment:

```
python workdir/train.py
```

Output format:
```
---
metric: 0.9771
training_seconds: 58.3
total_seconds: 60.1
peak_memory_mb: 123.4
num_params: 101770
num_steps: 15750
```

Parse the metric with: `grep "^metric:" run.log`

## Insights

- Baseline MLP (128h ReLU) achieves ~0.977 accuracy.
- Fixed 60s training budget across all experiments.
- MNIST data cached at ~/.cache/autoresearch-mnist/.
