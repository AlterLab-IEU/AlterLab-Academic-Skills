"""No dangling shared/ or scripts/ cross-references, and example payloads validate.

Two guarantees:

1. Every `shared/*.md`, `shared/schemas/*.schema.json`, and skill-local `scripts/*.py`
   citation in ANY SKILL.md body resolves to a real file on disk (the cross-skill
   handoff contracts and helper scripts skills link to must actually exist).

2. Every example handoff payload under `skills/core/shared/schemas/examples/` validates
   against its `*.schema.json` contract. jsonschema is not a project dependency, so a
   minimal stdlib validator covers the constructs these schemas actually use
   (type / required / enum / min|maxItems / minimum|maximum / properties / items / $ref).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCHEMAS_DIR = SKILLS_DIR / "core" / "shared" / "schemas"
EXAMPLES_DIR = SCHEMAS_DIR / "examples"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_skills  # noqa: E402


# --------------------------------------------------------------------------- #
# Part 1: shared/ + scripts/ cross-references resolve
# --------------------------------------------------------------------------- #

def _shared_or_scripts_citations(body: str, skill_dir: Path) -> list[str]:
    """Citations that target shared/ or skill-local scripts/ — the subset this test owns."""
    missing = audit_skills.missing_references(body, skill_dir)
    return [m for m in missing if "shared/" in m or m.startswith("scripts/") or "/scripts/" in m]


def test_every_shared_and_scripts_reference_resolves() -> None:
    """Scan every SKILL.md; no shared/ or scripts/ citation may dangle."""
    dangling: dict[str, list[str]] = {}
    for skill_md in sorted(SKILLS_DIR.rglob("SKILL.md")):
        _, body = audit_skills.parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        bad = _shared_or_scripts_citations(body, skill_md.parent)
        if bad:
            dangling[str(skill_md.relative_to(REPO_ROOT))] = bad
    assert not dangling, (
        "SKILL.md files cite shared/ or scripts/ paths that do not exist on disk: "
        f"{dangling}. Create the files or fix the citations."
    )


# --------------------------------------------------------------------------- #
# Part 2: minimal JSON Schema validator for the example payloads
# --------------------------------------------------------------------------- #

_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
}


def _resolve_ref(ref: str, root: dict) -> dict:
    """Resolve a local `#/$defs/foo` JSON pointer against the schema root."""
    assert ref.startswith("#/"), f"only local refs supported, got {ref!r}"
    node: object = root
    for part in ref[2:].split("/"):
        node = node[part]  # type: ignore[index]
    return node  # type: ignore[return-value]


def _validate(instance: object, schema: dict, root: dict, path: str) -> list[str]:
    """Return a list of human-readable validation errors (empty == valid)."""
    errors: list[str] = []

    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], root)

    expected = schema.get("type")
    if expected:
        py = _TYPE_MAP[expected]
        # JSON booleans are ints in Python; guard so True is not accepted as integer.
        if expected in ("integer", "number") and isinstance(instance, bool):
            errors.append(f"{path}: expected {expected}, got boolean")
            return errors
        if not isinstance(instance, py):
            errors.append(f"{path}: expected {expected}, got {type(instance).__name__}")
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")

    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property {req!r}")
        props = schema.get("properties", {})
        for key, sub in props.items():
            if key in instance:
                errors.extend(_validate(instance[key], sub, root, f"{path}.{key}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: {len(instance)} items < minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: {len(instance)} items > maxItems {schema['maxItems']}")
        item_schema = schema.get("items")
        if item_schema:
            for i, el in enumerate(instance):
                errors.extend(_validate(el, item_schema, root, f"{path}[{i}]"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: {instance} > maximum {schema['maximum']}")

    return errors


def _example_files() -> list[Path]:
    return sorted(EXAMPLES_DIR.glob("*.example.json"))


def test_examples_directory_is_populated() -> None:
    examples = _example_files()
    assert examples, (
        f"no example payloads found under {EXAMPLES_DIR.relative_to(REPO_ROOT)} — "
        "add at least one *.example.json validating a handoff schema."
    )


@pytest.mark.parametrize(
    "example",
    _example_files(),
    ids=[p.name for p in _example_files()],
)
def test_example_validates_against_schema(example: Path) -> None:
    """Each `<name>.example.json` validates against `<name>.schema.json`."""
    schema_name = example.name.replace(".example.json", ".schema.json")
    schema_path = SCHEMAS_DIR / schema_name
    assert schema_path.exists(), (
        f"{example.name} has no sibling schema {schema_name} in "
        f"{SCHEMAS_DIR.relative_to(REPO_ROOT)}"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    instance = json.loads(example.read_text(encoding="utf-8"))
    errors = _validate(instance, schema, schema, schema_name)
    assert not errors, f"{example.name} fails {schema_name}:\n" + "\n".join(errors)
