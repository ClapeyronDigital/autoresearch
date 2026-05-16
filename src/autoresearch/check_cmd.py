import json
import os
import subprocess
import sys

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
    ("import evaluate from eval",
     "from eval.evaluate import evaluate"),
    ("evaluate(Model()) returns float",
     "from workdir.model import Model\nfrom eval.evaluate import evaluate\n"
     "result = evaluate(Model())\n"
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

print(json.dumps(results))
"""


def run(target: str) -> int:
    target = os.path.abspath(target)

    if not os.path.isdir(target):
        print(f"Error: directory not found: {target}")
        return 1

    script = CHECK_SCRIPT.format(path=target)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )

    if proc.returncode != 0 and not proc.stdout.strip():
        print("Error: check script failed to run:")
        print(proc.stderr)
        return 1

    try:
        results = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        print("Error: invalid output from check script:")
        print(proc.stdout)
        print(proc.stderr)
        return 1

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

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1
