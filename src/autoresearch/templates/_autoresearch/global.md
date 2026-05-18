# Autoresearch Framework — Global Rules

You are an AI agent running automated experiments. Your goal is to iteratively
improve a measurable metric by editing code and running evaluations.

## Setup

Before starting, read the project context:
- `.autoresearch/project.md` — project description, contracts, baseline, insights
- `.autoresearch/config.yaml` — framework parameters (e.g. `max_experiments`)

Then set up the session:

1. Check existing branches to determine the next available session tag:
   ```
   git branch --list 'autoresearch/*'
   ```
   - If no `autoresearch/*` branches exist, start with `run1`.
   - Otherwise, find the highest existing `runN` number and increment it
     (e.g. `run1` → `run2`, `run3` → `run4`).

2. Create a branch:
   ```
   git checkout -b autoresearch/<tag>
   ```
3. Create the session directory:
   ```
   mkdir -p runs/<tag>/
   ```
4. Initialize `runs/<tag>/results.tsv` with the header:
   ```
   commit	metric	status	description	reasoning
   ```

## Permissions

**You CAN edit:**
- Everything inside `workdir/` — create, modify, delete any files

**You CANNOT edit:**
- `eval/` — evaluation logic is fixed
- `abstract/` — base classes are fixed
- `.autoresearch/` — project context and config are fixed
- External datasets (if any)

## Experiment Loop

Repeat up to `max_experiments` times (from `config.yaml`; 0 = unlimited):

### Step 1: Hypothesis

Decide what to try. Formulate a **reasoning** — why this change could improve the metric.
Keep it brief (1-2 sentences).

### Step 2: Edit

Modify files in `workdir/`. You have full freedom:
- Change the `Model` class architecture
- Add/remove/modify any modules in `workdir/`
- The model may be trainable or not — you decide

**Only requirement:** `workdir/model.py` must expose a `Model` class that inherits
`abstract.ModelBase` and implements `predict()`.

### Step 3: Commit

```
git add workdir/
git commit -m "brief description of the hypothesis"
```

### Step 4: Run Evaluation

You must evaluate the model by directly running the standard evaluation script. Custom evaluation runners in `workdir/` are strictly prohibited to ensure fair and consistent evaluation.

Run the evaluation like this:

```
python eval/evaluate.py
```

### Step 5: Extract Metric

Parse the output. Look for lines matching `^metric:` after the `---` delimiter.
The format is:

```
---
metric: 0.9771
```

The number is a float. Higher is better.

### Step 6: Record Result

Append a tab-separated row to `runs/<tag>/results.tsv`:

```
<commit_hash>	<metric>	<status>	<description>	<reasoning>
```

Columns:
- `commit` — 7-char short git hash
- `metric` — float, 4 decimal places
- `status` — `keep`, `discard`, or `crash`
- `description` — what was changed (brief)
- `reasoning` — why this hypothesis was tested

### Step 7: Decide

Compare the new metric against the current best:

- **metric > best_metric** → `keep` status. The commit stays. Update best_metric.
- **metric <= best_metric** → `discard` status. Revert:
  ```
  git reset --hard HEAD~1
  ```
- **Crash / error** → `crash` status. Read the error, try to fix, then revert:
  ```
  git reset --hard HEAD~1
  ```

## Crash Handling

If the evaluation crashes:
1. Read the error output (last ~50 lines).
2. Try to fix the issue in `workdir/`.
3. You may retry up to 2 times per experiment.
4. If still failing: mark as `crash`, revert, move on.

## Simplicity Criterion

When two experiments achieve the same metric, prefer the simpler one:
- Delete unnecessary code and keep the metric = keep
- Add complex/hacky code for a tiny gain = discard

## Completion

When `max_experiments` is reached or the session is interrupted:

1. Write `runs/<tag>/summary.md` with:
   - Session overview (total experiments, best metric, improvement)
   - Best experiments with descriptions
   - Key findings and insights

2. Generate the progress chart:
   ```
   autoresearch analyze --session <tag>
   ```

3. Optionally: update `.autoresearch/project.md` with new baseline and insights.

## Never Stop

Work autonomously. Do not ask for confirmation between experiments.
Run overnight if needed. Every experiment is one commit, one evaluation,
one decision.
