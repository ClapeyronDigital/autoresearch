import json
import os
import subprocess
import sys
import tempfile

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates", "_autoresearch")

with open(os.path.join(TEMPLATES_DIR, "global.md")) as f:
    DEFAULT_GLOBAL = f.read()
with open(os.path.join(TEMPLATES_DIR, "project.md")) as f:
    DEFAULT_PROJECT = f.read()

CHECK_SCRIPT = r"""
import json, os, sys, traceback

path = os.path.abspath({path!r})
sys.path.insert(0, path)
os.chdir(path)

results = []

checks = [
    ("import abstract base classes",
     "from abstract import ModelBase, EvaluatorBase"),
    ("import Model from workdir",
     "from workdir.model import Model"),
    ("Model inherits ModelBase",
     "from abstract import ModelBase\nfrom workdir.model import Model\n"
     "assert issubclass(Model, ModelBase), 'Model must inherit ModelBase'"),
    ("instantiate Model",
     "from workdir.model import Model\nModel()"),
    ("import Evaluator from eval",
     "from eval.evaluate import Evaluator"),
    ("Evaluator().evaluate(Model()) returns float",
     "from workdir.model import Model\nfrom eval.evaluate import Evaluator\n"
     "result = Evaluator().evaluate(Model())\n"
     "assert isinstance(result, float), "
     "f'Expected float, got {{type(result).__name__}}'"),
]

for name, code in checks:
    try:
        exec(compile(code, "<check>", "exec"))
        results.append({{"check": name, "pass": True}})
    except Exception:
        tb = traceback.format_exc().strip().split("\n")[-1]
        results.append({{"check": name, "pass": False, "error": tb}})

with open({json_path!r}, "w") as f:
    json.dump(results, f)
"""


def _print_warnings(target: str):
    """Check prompt files and print [WARN] lines if something is off."""
    # global.md — warn if modified
    global_path = os.path.join(target, ".autoresearch", "global.md")
    if os.path.isfile(global_path):
        with open(global_path) as f:
            content = f.read()
        if content != DEFAULT_GLOBAL:
            print("  [WARN] global.md has been modified from the default. Verify this was intentional.")
    else:
        print(f"  [WARN] .autoresearch/global.md not found")

    # project.md — warn if still default (user hasn't filled it in)
    project_path = os.path.join(target, ".autoresearch", "project.md")
    if os.path.isfile(project_path):
        with open(project_path) as f:
            content = f.read()
        if content == DEFAULT_PROJECT:
            print("  [WARN] project.md contains the default template. Fill it with your project details.")
    else:
        print(f"  [WARN] .autoresearch/project.md not found")


def run(target: str) -> int:
    target = os.path.abspath(target)

    if not os.path.isdir(target):
        print(f"Error: directory not found: {target}")
        return 1

    # Create temp file for passing results out of the subprocess
    fd, json_tmp = tempfile.mkstemp(suffix=".json", prefix="autoresearch_check_")
    os.close(fd)

    try:
        script = CHECK_SCRIPT.format(path=target, json_path=json_tmp)
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True,
        )

        if proc.returncode != 0 and not os.path.isfile(json_tmp):
            print("Error: check script failed to run:")
            print(proc.stderr)
            return 1

        if not os.path.isfile(json_tmp):
            print("Error: check script produced no output")
            print(proc.stdout)
            print(proc.stderr)
            return 1

        with open(json_tmp) as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        print("Error: invalid output from check script:")
        print(e)
        return 1
    finally:
        if os.path.isfile(json_tmp):
            os.remove(json_tmp)

    passed = 0
    failed = 0
    for r in results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  [{status}] {r['check']}")
        if not r["pass"]:
            print(f"          {r['error']}")
            failed += 1
        else:
            passed += 1

    _print_warnings(target)

    # Print any [WARN] messages from user code (e.g. stub warnings in model.py / evaluate.py)
    for line in proc.stdout.splitlines():
        if "  [WARN]" in line:
            print(line)

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1
