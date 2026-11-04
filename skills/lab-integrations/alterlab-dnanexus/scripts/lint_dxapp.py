#!/usr/bin/env python3
"""Lint a DNAnexus app/applet directory offline — no DNAnexus login, no network.

`dx build` validates most of dxapp.json on the server, and even `dx build --dry-run`
needs a login and a project context. This lint catches the common mistakes first:

  * dxapp.json parses and has name / runSpec / inputSpec / outputSpec
  * every input/output `class` is a DNAnexus class (int, float, string, boolean, hash,
    record, file, applet, and array:<class> except array:hash); class names are lower case
  * runSpec.interpreter is python3 or bash; runSpec.distribution/release/version is a
    supported execution environment (Ubuntu 24.04 or 20.04, version "0")
  * runSpec.file exists; for python3 apps the @dxpy.entry_point("main") function's
    parameters match inputSpec names, and the keys it returns match outputSpec names
  * instanceType and instanceTypeSelector are not both set (dxpy's own client check)

Supported releases and classes were read from documentation.dnanexus.com on 2026-10-22;
re-check them there when the lint disagrees with the platform.

  python3 lint_dxapp.py path/to/applet_dir      # exit 0 clean, 1 problems, 2 bad input
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

BASE = {"int", "float", "string", "boolean", "hash", "record", "file", "applet"}
CLASSES = BASE | {f"array:{c}" for c in BASE - {"hash"}}
INTERPRETERS = {"python3", "bash"}
RELEASES = {("Ubuntu", "24.04"), ("Ubuntu", "20.04")}


def _entry_point(tree: ast.Module, name: str = "main") -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") == "entry_point"
                        and dec.args and isinstance(dec.args[0], ast.Constant)
                        and dec.args[0].value == name):
                    return node
    return None


def _returned_keys(fn: ast.FunctionDef) -> set[str] | None:
    keys: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            keys |= {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    return keys or None


def lint(app_dir: Path) -> list[str]:
    spec_path = app_dir / "dxapp.json"
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"{spec_path}: not found"]
    except json.JSONDecodeError as exc:
        return [f"{spec_path}: invalid JSON ({exc})"]
    problems = [f"missing required field '{k}'" for k in ("name", "runSpec")
                if k not in spec]
    for io in ("inputSpec", "outputSpec"):
        if io not in spec:
            problems.append(f"missing '{io}' (an empty list is allowed)")
        for param in spec.get(io, []):
            cls = param.get("class")
            if cls not in CLASSES:
                hint = f" (use '{cls.lower()}')" if isinstance(cls, str) and cls.lower() in CLASSES else ""
                problems.append(f"{io}.{param.get('name')}: class {cls!r} is not a DNAnexus class{hint}")
    rs = spec.get("runSpec", {})
    if rs.get("interpreter") not in INTERPRETERS:
        problems.append(f"runSpec.interpreter {rs.get('interpreter')!r}: use python3 or bash")
    if (rs.get("distribution"), str(rs.get("release"))) not in RELEASES:
        problems.append(f"runSpec distribution/release {rs.get('distribution')!r}/{rs.get('release')!r}: "
                        "supported are Ubuntu 24.04 and Ubuntu 20.04")
    if str(rs.get("version", "0")) != "0":
        problems.append(f"runSpec.version {rs.get('version')!r}: use \"0\"")
    for entry, req in (rs.get("systemRequirements") or {}).items():
        if isinstance(req, dict) and "instanceType" in req and "instanceTypeSelector" in req:
            problems.append(f"systemRequirements.{entry}: instanceType and instanceTypeSelector are exclusive")
    src = app_dir / rs.get("file", "")
    if not rs.get("file") or not src.is_file():
        problems.append(f"runSpec.file {rs.get('file')!r} not found under {app_dir}")
    elif str(rs.get("interpreter", "")).startswith("python"):
        try:
            tree = ast.parse(src.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            return problems + [f"{src}: syntax error ({exc})"]
        main = _entry_point(tree)
        if main is None:
            problems.append(f"{src}: no @dxpy.entry_point('main') function")
        else:
            params = {a.arg for a in main.args.args + main.args.kwonlyargs}
            inputs = {p.get("name") for p in spec.get("inputSpec", [])}
            for missing in sorted(inputs - params):
                problems.append(f"inputSpec '{missing}' is not a parameter of main()")
            for extra in sorted(params - inputs):
                problems.append(f"main() parameter '{extra}' has no inputSpec entry")
            returned = _returned_keys(main)
            outputs = {p.get("name") for p in spec.get("outputSpec", [])}
            if returned is not None:
                for missing in sorted(outputs - returned):
                    problems.append(f"outputSpec '{missing}' is never returned by main()")
                for extra in sorted(returned - outputs):
                    problems.append(f"main() returns '{extra}', which outputSpec does not declare")
        if "dxpy.run()" not in src.read_text(encoding="utf-8"):
            problems.append(f"{src}: no dxpy.run() call at module level")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("app_dir", type=Path, help="directory that holds dxapp.json")
    args = ap.parse_args()
    if not args.app_dir.is_dir():
        print(f"error: {args.app_dir} is not a directory", file=sys.stderr)
        return 2
    problems = lint(args.app_dir)
    for p in problems:
        print(f"PROBLEM: {p}")
    print(f"{len(problems)} problem(s) in {args.app_dir / 'dxapp.json'} (offline lint; "
          "dx build still validates on the server)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
