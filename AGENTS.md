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
autoresearch init [path]              # scaffold new project from templates/
autoresearch check [path]             # 6 import/inheritance/return-type checks
autoresearch analyze --session NAME   # generate runs/<NAME>/progress.png from results.tsv
```

## Architecture

- **Package**: `src/autoresearch/` (src layout), built with `hatchling`
- **CLI entry**: `cli.py:main` → dispatches to `init_cmd`, `check_cmd`, `analyze_cmd`
- **Templates**: `src/autoresearch/templates/` — `init` copies these into the target project. Underscore-prefixed dirs (`_autoresearch`, `_gitignore`) are renamed to dot-prefixed (`.autoresearch`, `.gitignore`)
- **Abstract base classes**: `ModelBase`, `EvaluatorBase` live in `templates/abstract/__init__.py`
- **`check` command** runs 6 checks as a separate subprocess (`subprocess.run` with `exec`) and pipes results through a temp JSON file. It names `Evaluator` (not `MyEvaluator`)
- **`analyze`** depends on `matplotlib>=3.5` and reads tab-separated `results.tsv`

## Project structure (scaffolded)

| Dir | Edited by | Contents |
|-----|-----------|----------|
| `.autoresearch/` | Human | `global.md` (agent rules), `project.md`, `config.yaml` |
| `abstract/` | Nobody | `ModelBase`, `EvaluatorBase` |
| `eval/` | Human | `evaluate.py` → fixed metric |
| `workdir/` | Agent | `model.py`, training code, any modules |
| `runs/` | Gitignored | `results.tsv`, `progress.png`, `summary.md` |

## Branches

- `main` — the framework (autoresearch tool itself)
- Experimental branches (e.g. `mnist`) — each scaffolds a project for a specific task, installs `autoresearch` from GitHub as a dependency

## Gitignored paths

`dist/`, `runs/`, `uv.lock`, `results.tsv`, `run.log`, `examples/`
