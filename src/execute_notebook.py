from __future__ import annotations

import contextlib
import io
import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks" / "integrated_client_analytics_capstone.ipynb"
EXECUTED = ROOT / "notebooks" / "integrated_client_analytics_capstone.executed.ipynb"


def main():
    notebook = json.loads(SOURCE.read_text(encoding="ascii"))
    original_cwd = Path.cwd()
    execution_count = 0
    try:
        os.chdir(SOURCE.parent)
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            execution_count += 1
            source = "".join(cell.get("source", [])).strip()
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                if source.startswith("%run "):
                    target = (SOURCE.parent / source[5:].strip()).resolve()
                    sys.path.insert(0, str(target.parent))
                    try:
                        runpy.run_path(str(target), run_name="__main__")
                    finally:
                        sys.path.pop(0)
                elif source:
                    exec(compile(source, str(SOURCE), "exec"), {})
            cell["execution_count"] = execution_count
            cell["outputs"] = []
            if stdout.getvalue():
                cell["outputs"].append({
                    "name": "stdout", "output_type": "stream",
                    "text": stdout.getvalue().splitlines(keepends=True),
                })
            if stderr.getvalue():
                cell["outputs"].append({
                    "name": "stderr", "output_type": "stream",
                    "text": stderr.getvalue().splitlines(keepends=True),
                })
    finally:
        os.chdir(original_cwd)
    EXECUTED.write_text(json.dumps(notebook, indent=1), encoding="ascii")
    print(f"Executed {execution_count} code cell(s): {EXECUTED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
