"""
Plot experiment progress from results.tsv.
Only includes 'keep' experiments (improvements), discards and crashes are skipped.
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

rows = []
with open(TSV_FILE) as f:
    lines = f.read().strip().splitlines()

if len(lines) < 2:
    print("ERROR: no data rows in results.tsv")
    sys.exit(1)

header = lines[0].split("\t")
for line in lines[1:]:
    parts = line.split("\t")
    if len(parts) < 5:
        continue
    commit, val_acc, mem, status, desc = parts[0], parts[1], parts[2], parts[3], parts[4]
    if status == "keep":
        rows.append((commit, float(val_acc), desc))

if not rows:
    print("No 'keep' experiments found in results.tsv")
    sys.exit(0)

x = list(range(1, len(rows) + 1))
y = [r[1] for r in rows]

plt.figure(figsize=(10, 5))
plt.plot(x, y, "o-", markersize=4, linewidth=1.5)
plt.xlabel("Experiment (keep only)")
plt.ylabel("val_accuracy")
plt.title("MNIST Autoresearch Progress")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=150)
print(f"Saved {OUTPUT_FILE} ({len(rows)} keep experiments, best: {max(y):.4f})")
