"""
Plot experiment progress from results.tsv.
Shows both all experiments and keep-only progression on one chart.
Usage: uv run analysis.py
Output: progress.png
"""

import os
import sys
import matplotlib.pyplot as plt

TSV_FILE = "results.tsv"
OUTPUT_FILE = "progress.png"

if not os.path.exists(TSV_FILE):
    print(f"ERROR: {TSV_FILE} not found. Run some experiments first.")
    sys.exit(1)

with open(TSV_FILE) as f:
    lines = f.read().strip().splitlines()

if len(lines) < 2:
    print("ERROR: no data rows in results.tsv")
    sys.exit(1)

all_x, all_y, all_status = [], [], []
keep_x, keep_y, keep_desc = [], [], []

for i, line in enumerate(lines[1:], start=1):
    parts = line.split("\t")
    if len(parts) < 5:
        continue
    acc = float(parts[1])
    status = parts[3]
    all_x.append(i)
    all_y.append(acc)
    all_status.append(status)
    if status == "keep":
        keep_x.append(i)
        keep_y.append(acc)
        keep_desc.append(parts[4])

if not all_x:
    print("No experiments found in results.tsv")
    sys.exit(0)

fig, ax = plt.subplots(figsize=(12, 6))

# All experiments: scatter with color by status
colors = {"keep": "#2ecc71", "discard": "#e74c3c", "crash": "#95a5a6"}
for s in ("keep", "discard", "crash"):
    xs = [all_x[j] for j in range(len(all_x)) if all_status[j] == s]
    ys = [all_y[j] for j in range(len(all_x)) if all_status[j] == s]
    if xs:
        ax.scatter(xs, ys, c=colors[s], label=f"{s} ({len(xs)})", s=30, zorder=2, alpha=0.7)

# Keep-only progression line
if keep_x:
    ax.plot(keep_x, keep_y, "o-", color="#2ecc71", markersize=6, linewidth=2,
            label=f"keep progression (best: {max(keep_y):.4f})", zorder=3)

ax.set_xlabel("Experiment #")
ax.set_ylabel("val_accuracy")
ax.set_title("MNIST Autoresearch Progress")
ax.legend(loc="lower right", fontsize=8)
ax.grid(True, alpha=0.3)
ax.set_xlim(0.5, len(all_x) + 0.5)
fig.tight_layout()
fig.savefig(OUTPUT_FILE, dpi=150)
print(f"Saved {OUTPUT_FILE} ({len(all_x)} total, {len(keep_x)} keep, best: {max(all_y):.4f})")
