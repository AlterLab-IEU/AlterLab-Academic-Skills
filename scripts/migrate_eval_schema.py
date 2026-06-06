#!/usr/bin/env python3
"""Migrate per-skill eval files to the canonical agentskills.io eval shape.

Rewrites the legacy `{query, expected_behavior, should_trigger}` eval shape in place
to the canonical shape defined by docs/evals.schema.json:

    legacy eval                      canonical eval
    -----------                      --------------
    query              ->            prompt
    expected_behavior  ->            expected_output
    should_trigger:    ->            assertions: [{type: should_trigger,     value: true}]   (when true)
    should_trigger:    ->            assertions: [{type: should_not_trigger, value: true}]   (when false)
    id                 ->            id (unchanged)

`should_trigger` survives as an assertion type, so behavioral coverage does not regress.
The migration is idempotent: files already on the canonical shape are reported as
"already canonical" and left untouched.

    uv run python scripts/migrate_eval_schema.py            # migrate the 6 core files in place
    uv run python scripts/migrate_eval_schema.py --check    # report what would change; exit 1 if any need migration
    uv run python scripts/migrate_eval_schema.py --validate # after migrating, validate against docs/evals.schema.json (needs jsonschema)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
SCHEMA_PATH = REPO / "docs" / "evals.schema.json"

LEGACY_KEYS = {"query", "expected_behavior", "should_trigger"}


def is_legacy_eval(e: dict) -> bool:
    """A legacy eval has query/expected_behavior/should_trigger and no canonical keys."""
    return ("query" in e or "expected_behavior" in e or "should_trigger" in e) and (
        "prompt" not in e and "expected_output" not in e
    )


def migrate_eval(e: dict) -> dict:
    """Convert one legacy eval dict to the canonical shape, preserving id and any extras."""
    out: dict = {}
    if "id" in e:
        out["id"] = e["id"]
    out["prompt"] = e.get("query", e.get("prompt", ""))
    out["expected_output"] = e.get("expected_behavior", e.get("expected_output", ""))

    # Carry through optional canonical fields if already present.
    if "files" in e:
        out["files"] = e["files"]

    assertions = list(e.get("assertions", []))
    should = e.get("should_trigger")
    if isinstance(should, bool):
        atype = "should_trigger" if should else "should_not_trigger"
        # Avoid duplicating a trigger assertion if one already exists.
        if not any(a.get("type") in {"should_trigger", "should_not_trigger"} for a in assertions):
            assertions.insert(0, {"type": atype, "value": True})
    if assertions:
        out["assertions"] = assertions
    return out


def migrate_file(path: Path) -> tuple[bool, str]:
    """Return (changed, message). Writes the migrated file in place when changed."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (False, f"invalid JSON: {exc}")

    evals = data.get("evals")
    if not isinstance(evals, list):
        return (False, "missing or non-list 'evals'")

    if not any(is_legacy_eval(e) for e in evals if isinstance(e, dict)):
        return (False, "already canonical")

    new_evals = [migrate_eval(e) if isinstance(e, dict) else e for e in evals]
    out = {"skill": data.get("skill", path.parent.parent.name), "evals": new_evals}
    # Preserve any other top-level metadata keys (forward-compatible).
    for k, v in data.items():
        if k not in ("skill", "evals"):
            out[k] = v

    path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return (True, f"migrated {len(new_evals)} eval(s)")


def validate_file(path: Path, validator) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [f"{list(err.path)}: {err.message}" for err in validator.iter_errors(data)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if any file needs migration")
    ap.add_argument("--validate", action="store_true", help="validate migrated files against docs/evals.schema.json")
    ap.add_argument("paths", nargs="*", help="explicit eval files (default: skills/core/*/evals/evals.json)")
    args = ap.parse_args()

    if args.paths:
        files = [Path(p).resolve() for p in args.paths]
    else:
        files = sorted((SKILLS / "core").glob("*/evals/evals.json"))

    if not files:
        print("No eval files found.")
        return 0

    needs_migration = 0
    for f in files:
        rel = f.relative_to(REPO)
        if args.check:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                legacy = any(is_legacy_eval(e) for e in data.get("evals", []) if isinstance(e, dict))
            except json.JSONDecodeError as exc:
                print(f"  ! {rel}: invalid JSON: {exc}")
                needs_migration += 1
                continue
            if legacy:
                needs_migration += 1
                print(f"  ~ {rel}: NEEDS migration")
            else:
                print(f"  = {rel}: already canonical")
        else:
            changed, msg = migrate_file(f)
            mark = "->" if changed else "=="
            print(f"  {mark} {rel}: {msg}")

    if args.check:
        print(f"\n{needs_migration} file(s) need migration.")
        return 1 if needs_migration else 0

    if args.validate:
        try:
            from jsonschema import Draft202012Validator
        except ModuleNotFoundError:
            print("\njsonschema not installed; skipping validation. "
                  "Run: uv run --with jsonschema python scripts/migrate_eval_schema.py --validate")
            return 0
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        bad = 0
        print("\nValidating against docs/evals.schema.json:")
        for f in files:
            errs = validate_file(f, validator)
            if errs:
                bad += 1
                print(f"  X {f.relative_to(REPO)}:")
                for e in errs:
                    print(f"      {e}")
            else:
                print(f"  OK {f.relative_to(REPO)}")
        print(f"\n{len(files)} file(s), {bad} invalid.")
        return 1 if bad else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
