import os
import shutil

DOT_RENAMES = {"_autoresearch": ".autoresearch", "_gitignore": ".gitignore"}


def run(target: str) -> int:
    target = os.path.abspath(target)
    templates = os.path.join(os.path.dirname(__file__), "templates")

    _copy_recursive(templates, target)
    print(f"Done. Edit eval/evaluate.py and .autoresearch/project.md, then run:\n"
          f"  autoresearch check")
    return 0


def _copy_recursive(src: str, dst: str):
    os.makedirs(dst, exist_ok=True)

    with os.scandir(src) as entries:
        for entry in sorted(entries, key=lambda e: e.name):
            name = entry.name
            dst_name = DOT_RENAMES.get(name, name)
            dst_path = os.path.join(dst, dst_name)

            if entry.is_dir():
                _copy_recursive(entry.path, dst_path)
            else:
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(entry.path, dst_path)
                print(f"  Created {dst_path}")
