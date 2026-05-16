# autoresearch-mnist

This is a toy experiment in autonomous ML research: an AI agent iterates on a neural network for MNIST digit classification.

## Setup

To set up a new experiment, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `may16`). The branch `autoresearch/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**: The repo is small. Read these files for full context:
   - `prep_mnist.py` — fixed constants, data loading, evaluation. Do not modify.
   - `train_mnist.py` — the file you modify. Model architecture, optimizer, training loop.
4. **Verify data exists**: Check that `~/.cache/autoresearch-mnist/` contains MNIST data. If not, tell the human to run `uv run prep_mnist.py`.
5. **Initialize results.tsv**: Create `results.tsv` with just the header row. The baseline will be recorded after the first run.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

**MAX_EXPERIMENTS = 30**   *(set to 0 for unlimited)*

Each experiment runs on the local machine (CPU, MPS, or CUDA — auto-detected). The training script runs for a **fixed time budget of 60 seconds** (wall clock training time). You launch it simply as: `uv run train_mnist.py`.

**What you CAN do:**
- Modify `train_mnist.py` — this is the only file you edit. Everything is fair game: model architecture, optimizer, hyperparameters, training loop, batch size, learning rate schedule, etc.
- Rewrite the `Model` class entirely — switch from MLP to CNN, add residual connections, change activations, add dropout/batch norm, etc.
- Add data augmentation inside the training loop (e.g. random transforms applied to input tensors).
- Add learning rate schedules, gradient clipping, label smoothing, etc.

**What you CANNOT do:**
- Modify `prep_mnist.py`. It is read-only. It contains the fixed evaluation and data loading.
- Modify the evaluation function. `evaluate_accuracy` in `prep_mnist.py` is the ground truth metric.
- Install new packages or add dependencies. You can only use what's already in `pyproject.toml` (torch, torchvision).
- Change the dataset. MNIST is fixed — 60k train, 10k test.

**The goal is simple: get the highest val_accuracy.** Since the time budget is fixed at 60 seconds, every experiment gets equal compute. Everything is fair game: change the architecture, the optimizer, the hyperparameters, the batch size, the preprocessing. The only constraint is that the code runs without crashing and finishes within the time budget.

**Simplicity criterion**: All else being equal, simpler is better. A small accuracy improvement that adds ugly complexity is not worth it. Conversely, removing something and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the improvement magnitude. A 0.001 accuracy improvement that adds 20 lines of hacky code? Probably not worth it. A 0.001 accuracy improvement from deleting code? Definitely keep. An improvement of ~0 but much simpler code? Keep.

**The first run**: Your very first run should always be to establish the baseline, so you will run the training script as is.

## Output format

Once the script finishes it prints a summary like this:

```
---
val_accuracy: 0.9720
training_seconds: 58.3
total_seconds: 60.1
peak_memory_mb: 123.4
num_params: 101770
num_steps: 15750
```

Extract the key metric from the log file:

```
grep "^val_accuracy:" run.log
```

## Logging results

When an experiment is done, log it to `results.tsv` (tab-separated, NOT comma-separated — commas break in descriptions).

The TSV has a header row and 5 columns:

```
commit	val_accuracy	memory_mb	status	description
```

1. git commit hash (short, 7 chars)
2. val_accuracy achieved (e.g. 0.9720) — use 0.0000 for crashes
3. peak memory in MB, round to .1f — use 0.0 for crashes
4. status: `keep` (improved accuracy), `discard` (same or worse), or `crash`
5. short text description of what this experiment tried

Example:

```
commit	val_accuracy	memory_mb	status	description
a1b2c3d	0.9120	123.4	keep	baseline MLP
b2c3d4e	0.9340	130.2	keep	added 2nd hidden layer
c3d4e5f	0.9310	130.2	discard	switch to SGD
d4e5f6g	0.0000	0.0	crash	typo in Model init
e5f6g7h	0.9520	150.8	keep	replace MLP with small CNN
```

## The experiment loop

The experiment runs on a dedicated branch (e.g. `autoresearch/may16` or `autoresearch/may16-gpu0`).

LOOP (until MAX_EXPERIMENTS reached, if set):

1. **Check MAX_EXPERIMENTS**: If MAX_EXPERIMENTS > 0, count entries in `results.tsv` (excluding header). If >= MAX_EXPERIMENTS — stop the loop and print a final summary.
2. Look at the git state: the current branch/commit we're on
2. Tune `train_mnist.py` with an experimental idea by directly hacking the code.
3. git commit
4. Run the experiment: `uv run train_mnist.py > run.log 2>&1` (redirect everything — do NOT use tee or let output flood your context)
5. Read out the results: `grep "^val_accuracy:\|^peak_memory_mb:" run.log`
6. If the grep output is empty, the run crashed. Run `tail -n 50 run.log` to read the Python stack trace and attempt a fix. If you can't get things to work after more than a few attempts, give up.
7. Record the results in the tsv (NOTE: do not commit the results.tsv file, leave it untracked by git)
8. If val_accuracy improved (higher), you "advance" the branch, keeping the git commit
9. If val_accuracy is equal or worse, you git reset back to where you started

The idea is that you are a completely autonomous researcher trying things out. If they work, keep. If they don't, discard. And you're advancing the branch so that you can iterate. If you feel like you're getting stuck in some way, you can rewind but you should probably do this very very sparingly (if ever).

**Timeout**: Each experiment should take ~60 seconds total (training time budget + a few seconds for eval). If a run exceeds 2 minutes, kill it and treat it as a failure (discard and revert).

**Crashes**: If a run crashes (bug, misspelled variable, etc.), use your judgment: If it's something dumb and easy to fix (e.g. a typo, a missing import), fix it and re-run. If the idea itself is fundamentally broken, just skip it, log "crash" as the status in the tsv, and move on.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep, or gone from a computer and expects you to continue until MAX_EXPERIMENTS is reached or you are manually stopped. You are autonomous. If you run out of ideas, think harder — re-read the in-scope files for new angles, try combining previous near-misses, try more radical architectural changes (CNN, residual connections, different optimizers, learning rate schedules, etc.). The loop runs until MAX_EXPERIMENTS is reached or the human interrupts you, period.

As an example use case, a user might leave you running overnight with `MAX_EXPERIMENTS = 500`. If each experiment takes ~1 minute then you can run approx 60/hour, for a total of about 500 over the duration of the average human sleep. The user then wakes up to experimental results, all completed by you while they slept!

## Ideas to explore

If you ever feel stuck, here are some directions to try:

- **Architecture**: Replace MLP with a CNN (Conv2d + MaxPool2d + Linear). Add more conv layers. Try different kernel sizes. Add residual/skip connections.
- **Optimization**: Switch from Adam to SGD with momentum. Try AdamW. Tune learning rates. Add a learning rate schedule (cosine, step decay). Try gradient clipping.
- **Regularization**: Add dropout. Try different dropout rates. Add weight decay. Try label smoothing loss.
- **Data augmentation**: Add random affine transforms or random erasing inside the training loop.
- **Normalization**: Add BatchNorm1d or BatchNorm2d layers. Try LayerNorm.
- **Activations**: Try GELU, SiLU, LeakyReLU instead of ReLU.
- **Training**: Try different batch sizes (power of 2: 32, 64, 128, 256). Adjust the balance of batch size vs steps.
