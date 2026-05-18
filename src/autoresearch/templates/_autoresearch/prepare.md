# Prompt: Prepare a project for Autoresearch

You are a coding agent. Your task is to take an **existing user project** and prepare an **Autoresearch research sandbox** for it: describe the task, set up the metric, and implement a baseline so that a research agent can start running experiments.

Everything related to Autoresearch is isolated in a `research/` subdirectory, keeping it separate from the user's original source code.

---

## 0. How to work with the user

You work **in dialogue with the user**, but **only during this preparation stage**. Once `research/` is ready and handed off to the research agent, the experiments run autonomously with no user interaction.

If at any step you lack context or are unsure about a decision — **ask**. Better to clarify than to do it wrong.

Typical situations where you should ask:
- Unclear what metric measures quality for this task
- Unclear which test data to use
- The project has multiple possible metrics — which one is primary?
- `evaluate()` requires dependencies not present in the project
- External data needs to be downloaded — agree on the source
- Any other uncertainty

The user is your partner; they are invested in a correct setup.

---

## 1. What is Autoresearch (context for this work)

**Autoresearch** is a framework for automated research on tasks with a **numeric metric** (accuracy, MSE, BLEU, SNR, compression ratio, etc.). An AI agent iteratively improves the solution: hypothesis → edit code → measure metric → decide (keep / revert).

### Research sandbox structure

Inside `research/` after initialization:

```
research/
├── .autoresearch/
│   ├── prepare.md          ← this file (instructions for you)
│   ├── project.md          ← you need to fill this in (description + contract)
│   ├── global.md           ← rules for the research agent (already exists)
│   └── config.yaml         ← session parameters (already exists)
├── abstract/
│   └── __init__.py         ← ModelBase, EvaluatorBase (already exists, do NOT edit)
├── eval/
│   └── evaluate.py         ← you need to implement this (metric)
├── workdir/
│   └── model.py            ← you need to implement this (baseline model)
└── runs/                   ← session artifacts (created later)
```

The `research/` directory is created by running:
```bash
autoresearch init research   # run from the user's project root
```

Core files — `abstract/__init__.py`, `.autoresearch/global.md`, `.autoresearch/config.yaml` — are already copied. Do not edit them.

The user's project lives **outside**, one level up:
```
user-project/
├── research/               ← Autoresearch (you work here)
├── src/                    ← original user code
├── data/
├── README.md
├── AGENTS.md
├── pyproject.toml
└── ...
```

When implementing `eval/evaluate.py` and `workdir/model.py`, you can reference the user's code via `../` or copy relevant parts into `research/`.

### Model ↔ eval contract

- `Model` (in `workdir/model.py`) inherits `abstract.ModelBase` and implements `predict(self, x)`
- `Evaluator` (in `eval/evaluate.py`) inherits `abstract.EvaluatorBase`, implements `evaluate(self, model) → float`, and internally calls `model.predict()` on test data
- The metric is a **single float**; higher is better
- The contract between `predict()` and `evaluate()` (types of `x` and the return value) is described in `project.md`

---

## 2. Execution instructions

### Step 1. Study the user's project

Go up one level (to the user's project root) and read files to understand the task:

1. **`AGENTS.md`** — most likely place with task description
2. **`README.md`** — project description
3. **`pyproject.toml`** or **`package.json`** — project name, dependencies
4. Any other files — code, data, configs

Build an understanding of:
- What task is being solved? (classification, regression, generation, compression, signal processing, optimisation?)
- What are the inputs? (images, text, tables, signals, something else?)
- What is the expected output of the model? (class, scalar, sequence?)
- How is quality measured? (accuracy, MSE, BLEU, PSNR, F1, IoU, something custom?)
- Is there test data available for evaluation? (test set, files, generator?)
- Is there any existing model or algorithm code?

**If questions remain after studying the project — ask the user.**

### Step 2. Implement `eval/evaluate.py`

Create or overwrite [`eval/evaluate.py`](../eval/evaluate.py). It must contain a class `Evaluator` that inherits from `EvaluatorBase`.

**What evaluate() does:**
1. Loads test data (fixed in advance, no model training involved)
2. Calls `model.predict(x)` for each test sample
3. Computes the metric by comparing predictions against ground truth
4. Returns a `float` — higher is better

```python
from abstract import EvaluatorBase

class Evaluator(EvaluatorBase):
    def __init__(self):
        # Load test data (X_test, y_test)
        # Data must be fixed — the metric must be deterministic
        ...

    def evaluate(self, model) -> float:
        # Call model.predict() on test data
        predictions = model.predict(self.X_test)
        # Compute the metric
        metric = ...
        # Return float (higher is better)
        return float(metric)
```

**Requirements:**
- The metric must be **deterministic** — the same model always produces the same result
- `evaluate()` must not mutate the model's state (no training, no side effects)
- If the metric needs data not present inside `research/` — load it **inside `__init__`** (download, generate, read from a file). Data can be stored in `workdir/` or fetched from a reliable external source
- **Augmentations and randomness are forbidden** — every measurement must return the same result for the same model
- If the data lives in the user's project (e.g. `../data/test.csv`) — you can reference it via relative path. But prefer copying or symlinking the path into `research/` to keep the sandbox self-contained

### Step 3. Implement `workdir/model.py`

Create or overwrite [`workdir/model.py`](../workdir/model.py). It must contain a class `Model` that inherits from `ModelBase` with a `predict(self, x)` method.

This is the **baseline** — the simplest working version the research agent will build upon. For example:
- Constant prediction (mean, median, zero vector)
- Simple algorithm (k-NN, linear regression, threshold classifier)
- Stub if no baseline is needed yet
- The user's existing model code adapted to `ModelBase`

```python
from abstract import ModelBase

class Model(ModelBase):
    def predict(self, x):
        # Baseline: simplest working solution
        # Must be compatible with what Evaluator.evaluate() expects
        ...
```

**Requirements:**
- `predict(x)` must be compatible with what `Evaluator.evaluate()` calls
- The model must not require lengthy training — this is a starting baseline
- You may train a simple model if training is fast (seconds). If training is slow — make a stub
- If the user's project contains an existing model — adapt it (wrap in a `Model` class, import via `sys.path`, or copy files)

### Step 4. Fill in `.autoresearch/project.md`

Open [`project.md`](project.md) (it lives next to this file, in `.autoresearch/`) and fill in each section.

#### Title
```markdown
# Project: <project name>
```
Take it from `pyproject.toml` → `[project].name`, or from `README.md`, or from `AGENTS.md`. If nothing is available — use the user's project root directory name.

#### Description
```markdown
## Description

Brief description of the task (2-4 sentences).
```
What the model does, what problem it solves, what data it uses. Keep it concise.

#### Contract: model ↔ eval
```markdown
## Contract: model ↔ eval

`Model.predict(x)` receives:
  - `x`: <type, shape, semantics>

Returns:
  - <type, shape, semantics>

`evaluate(model)` calls `model.predict()` on test data and returns a float
(higher is better).
```
**Describe as concretely as possible what is actually implemented in evaluate.py and model.py:**
- `x`: `numpy.ndarray` of shape `(784,)`? `torch.Tensor`? `str` (path)? `pd.DataFrame`? `list[float]`?
- Return value of `predict()`: `numpy.ndarray` of shape `(10,)` (logits)? `float` (scalar)? `int` (class index)?
- What test data does `evaluate()` use: where does it come from, how many samples, how is it preprocessed?

#### Baseline
```markdown
## Baseline

- Baseline metric: <value>
- Description of the baseline model/approach.
```
Run `eval/evaluate.py` and record the metric:
```bash
cd research
python eval/evaluate.py
```
From the output, extract the line `metric: <number>`. This is the baseline metric.

If the model is a stub returning dummy values — make sure evaluate at least runs, and record whatever number comes out. The research agent will update the baseline later when it produces the first real metric.

#### Insights
```markdown
## Insights

- <notes>
```
Record anything useful you've learned:
- Approaches the user has already tried
- Architectural constraints (CPU-only, no GPU, memory limits)
- Data characteristics (class imbalance, noise, missing values)
- If the user's project has an `AGENTS.md` with useful context — capture key points here
If there's nothing to write — leave the section empty.

### Step 5. Verify the result

Run the contract checks:
```bash
cd research
autoresearch check
```

Expected result: **6 PASS**. If any checks fail — fix the issues.

After a successful check, commit the initial state:
```bash
cd research
git init
git add -A
git commit -m "chore: init autoresearch project with baseline"
```

---

**Important.** Do NOT start experiments. Your only job is to prepare `research/` so that the research agent can read `project.md`, enter `research/`, and launch the first experiment session.
