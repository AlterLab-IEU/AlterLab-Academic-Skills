"""Loader-contract checks for the marketplace and the per-domain plugin manifests.

Each test pins a rule the Claude Code plugin loader enforces at install/load time — rules the
repo previously violated without any test noticing (verified against `claude plugin validate`
and a real install, 2026-09-23):

* `agents` takes agent FILES; a directory entry makes the marketplace entry invalid and the
  whole plugin uninstallable (`alterlab-core` could not be installed in v2.6.1).
* a `strict: false` entry is the entire plugin definition, so it must not coexist with a
  component-declaring `plugin.json` (`alterlab-social-science-workflow` failed to load).
* a marketplace entry rejects the file-path form of `hooks`; `hooks/hooks.json` at the plugin
  root is auto-discovered instead.
* every `${user_config.KEY}` an `.mcp.json` substitutes must be a declared `userConfig` option.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
COMPONENT_KEYS = {"skills", "commands", "agents", "workflows", "hooks", "mcpServers", "userConfig"}
USER_CONFIG_RE = re.compile(r"\$\{user_config\.([A-Za-z_][A-Za-z0-9_]*)\}")


def _entries() -> list[dict]:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))["plugins"]


def _root(entry: dict) -> Path:
    return REPO_ROOT / entry["source"].lstrip("./").rstrip("/")


def _manifest(entry: dict) -> dict:
    """The component-bearing manifest: the entry itself, or the plugin.json it defers to."""
    if entry.get("strict", True):
        return json.loads((_root(entry) / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return entry


@pytest.fixture(params=_entries(), ids=lambda e: e["name"])
def entry(request) -> dict:
    return request.param


def test_strict_entries_defer_to_plugin_json(entry: dict) -> None:
    has_plugin_json = (_root(entry) / ".claude-plugin" / "plugin.json").is_file()
    if entry.get("strict", True):
        assert has_plugin_json, f"{entry['name']}: strict entry needs a plugin.json"
        leaked = COMPONENT_KEYS & entry.keys()
        assert not leaked, f"{entry['name']}: strict entry should carry metadata only, found {leaked}"
    else:
        assert not has_plugin_json, (
            f"{entry['name']}: strict:false entry must not coexist with a plugin.json "
            "(conflicting manifests — the plugin fails to load)"
        )


def test_agents_are_existing_md_files(entry: dict) -> None:
    root = _root(entry)
    for path in _manifest(entry).get("agents", []):
        assert path.startswith("./") and path.endswith(".md"), (
            f"{entry['name']}: agents entry {path!r} must be a ./relative .md file, not a directory"
        )
        assert (root / path).is_file(), f"{entry['name']}: agent file {path} does not exist"


def test_hooks_not_declared_as_path_in_marketplace(entry: dict) -> None:
    hooks = entry.get("hooks")
    assert hooks is None or isinstance(hooks, dict), (
        f"{entry['name']}: marketplace entries reject the file-path/array form of `hooks`; "
        "rely on hooks/hooks.json auto-discovery or inline the object"
    )


def test_user_config_covers_mcp_placeholders(entry: dict) -> None:
    mcp = _root(entry) / ".mcp.json"
    if not mcp.is_file():
        pytest.skip("no .mcp.json")
    needed = set(USER_CONFIG_RE.findall(mcp.read_text(encoding="utf-8")))
    declared = _manifest(entry).get("userConfig", {})
    missing = needed - declared.keys()
    assert not missing, f"{entry['name']}: .mcp.json uses undeclared user_config keys {sorted(missing)}"
    for key, spec in declared.items():
        for field in ("type", "title", "description"):
            assert spec.get(field), f"{entry['name']}: userConfig.{key} lacks required `{field}`"


def test_declared_paths_exist(entry: dict) -> None:
    root = _root(entry)
    manifest = _manifest(entry)
    for key in ("skills", "commands"):
        for path in manifest.get(key, []):
            assert (root / path).exists(), f"{entry['name']}: {key} path {path} does not exist"
    for key in ("workflows", "mcpServers"):
        value = manifest.get(key)
        if isinstance(value, str):
            assert (root / value).exists(), f"{entry['name']}: {key} path {value} does not exist"
