# AGENTS.md

## Build & Run

```bash
uv sync                    # create venv, install deps
uv pip install -e .        # dev install (editable)
uv build                   # build sdist + wheel into dist/
```

Dev install alternative (CLI-focused):
```bash
uv tool install git+https://github.com/ClapeyronDigital/autoresearch.git
```

Commands after install:
```bash
autoresearch init [path]              # scaffold new research/ from templates/
autoresearch check [path]             # 6 import/inheritance/return-type checks
autoresearch analyze --session NAME   # generate runs/<NAME>/progress.png from results.tsv
```

## Workflow: two agent roles

Autoresearch uses **two distinct agent roles**, each with its own prompt:

### 1. Coding agent — project preparation

**Entry point:** `research/.autoresearch/prepare.md`

This agent takes the user's existing project and bootstraps an Autoresearch sandbox:
- Implements the metric in `research/eval/evaluate.py`
- Implements a baseline in `research/workdir/model.py`
- Fills in `research/.autoresearch/project.md`
- Runs `autoresearch check` to verify contracts

The coding agent works **in dialogue with the user** to resolve ambiguity.

**User prompt:**
```
Привет! Прочитай research/.autoresearch/prepare.md и приступай к работе!
```

### 2. Research agent — autonomous experiments

**Entry point:** `research/.autoresearch/global.md`

This agent runs the experiment loop autonomously (hypothesis → edit → commit → evaluate → decide).

**User prompt:**
```
Привет! Прочитай research/.autoresearch/global.md и приступай к работе!
```

## Architecture

- **Package**: `src/autoresearch/` (src layout), built with `hatchling`
- **CLI entry**: `cli.py:main` → dispatches to `init_cmd`, `check_cmd`, `analyze_cmd`
- **Templates**: `src/autoresearch/templates/` — `init` copies these into the target directory. Underscore-prefixed dirs (`_autoresearch`, `_gitignore`) are renamed to dot-prefixed (`.autoresearch`, `.gitignore`)
- **Abstract base classes**: `ModelBase`, `EvaluatorBase` live in `templates/abstract/__init__.py`
- **`check` command** runs 6 checks as a separate subprocess (`subprocess.run` with `exec`) and pipes results through a temp JSON file. It expects `Evaluator` (not `MyEvaluator`)
- **`analyze`** depends on `matplotlib>=3.5` and reads tab-separated `results.tsv`

## Templates (what `autoresearch init [path]` copies)

```
templates/
├── _autoresearch/
│   ├── prepare.md          → .autoresearch/prepare.md  (coding agent prompt)
│   ├── global.md           → .autoresearch/global.md   (research agent rules)
│   ├── project.md          → .autoresearch/project.md  (task description, contracts, baseline)
│   └── config.yaml         → .autoresearch/config.yaml (session params)
├── abstract/
│   └── __init__.py         → abstract/__init__.py  (ModelBase, EvaluatorBase)
├── eval/
│   └── evaluate.py         → eval/evaluate.py      (metric stub, to be filled by coding agent)
├── workdir/
│   └── model.py            → workdir/model.py       (baseline stub, to be filled by coding agent)
└── _gitignore              → .gitignore
```

## Research sandbox structure (after init + coding agent)

```
research/
├── .autoresearch/
│   ├── prepare.md            # Coding agent prompt
│   ├── global.md             # Research agent rules
│   ├── project.md            # Task description, contracts, baseline
│   └── config.yaml           # Session parameters
├── abstract/
│   └── __init__.py           # ModelBase, EvaluatorBase
├── eval/
│   └── evaluate.py           # Metric (implemented by coding agent)
├── workdir/
│   └── model.py              # Baseline model (implemented by coding agent)
└── runs/                     # Gitignored, created during experiments
```

## Project structure (user's perspective)

```
user-project/
├── research/                 ← Autoresearch sandbox (everything above)
├── src/                      ← original user code
├── data/
├── README.md
├── AGENTS.md
├── pyproject.toml
└── ...
```

## Branches

- `main` — the framework (autoresearch tool itself)
- Experimental branches (e.g. `mnist`) — each scaffolds a project for a specific task, installs `autoresearch` from GitHub as a dependency

## Gitignored paths

`dist/`, `runs/`, `uv.lock`, `results.tsv`, `run.log`, `examples/`
