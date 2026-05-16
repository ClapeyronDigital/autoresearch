"""Generate progress chart from a session's results.tsv."""

import os
import sys
import matplotlib.pyplot as plt


def run(target: str, session: str) -> int:
    target = os.path.abspath(target)
    tsv_path = os.path.join(target, "runs", session, "results.tsv")
    out_path = os.path.join(target, "runs", session, "progress.png")

    if not os.path.exists(tsv_path):
        print(f"Error: {tsv_path} not found. Run some experiments first.")
        return 1

    with open(tsv_path) as f:
        lines = f.read().strip().splitlines()

    if len(lines) < 2:
        print("Error: no data rows in results.tsv")
        return 1

    all_x, all_y, all_status = [], [], []
    keep_x, keep_y, keep_desc = [], [], []

    for i, line in enumerate(lines[1:], start=1):
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        metric = float(parts[1])
        status = _find_status(parts)
        if status is None:
            continue
        all_x.append(i)
        all_y.append(metric)
        all_status.append(status)
        if status == "keep":
            keep_x.append(i)
            keep_y.append(metric)
            keep_desc.append(parts[-1] if len(parts) > 4 else "")

    if not all_x:
        print("No experiments found in results.tsv")
        return 0

    fig, ax = plt.subplots(figsize=(12, 6))

    colors = {"keep": "#2ecc71", "discard": "#e74c3c", "crash": "#95a5a6"}
    for s in ("keep", "discard", "crash"):
        xs = [all_x[j] for j in range(len(all_x)) if all_status[j] == s]
        ys = [all_y[j] for j in range(len(all_x)) if all_status[j] == s]
        if xs:
            ax.scatter(xs, ys, c=colors[s], label=f"{s} ({len(xs)})",
                       s=30, zorder=2, alpha=0.7)

    if keep_x:
        ax.plot(keep_x, keep_y, "o-", color="#2ecc71", markersize=6, linewidth=2,
                label=f"keep progression (best: {max(keep_y):.4f})", zorder=3)

    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Metric")
    ax.set_title(f"Autoresearch Progress — {session}")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0.5, len(all_x) + 0.5)
    fig.tight_layout()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)

    print(f"Saved {out_path} ({len(all_x)} total, {len(keep_x)} keep, "
          f"best: {max(all_y):.4f})")
    return 0


STATUS_VALUES = {"keep", "discard", "crash"}


def _find_status(parts: list[str]) -> str | None:
    for p in parts:
        if p in STATUS_VALUES:
            return p
    return None
