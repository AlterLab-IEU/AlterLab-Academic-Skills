"""Validate bundled academic MCP manifests and their documentation.

Every `.mcp.json` shipped in the repo must:
  1. Be valid JSON with a non-empty `mcpServers` object.
  2. Give each server a runnable `command` and a list `args`.
  3. Have every server name documented in references/mcp_setup.md.

And, the other direction: the core/databases plugins are meant to bundle the same
four academic servers, so we assert the expected set is present and that the two
manifests stay in sync.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MCP_SETUP_DOC = SKILLS_DIR / "core" / "references" / "mcp_setup.md"

# The academic servers these plugins are contracted to bundle (ws-12b).
EXPECTED_SERVERS = {"pubmed", "openalex", "crossref", "zotero"}


def _mcp_manifests() -> list[Path]:
    return sorted(SKILLS_DIR.rglob(".mcp.json"))


def _load_servers(manifest: Path) -> dict:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{manifest} is not a JSON object"
    servers = data.get("mcpServers")
    assert isinstance(servers, dict) and servers, (
        f"{manifest} must have a non-empty 'mcpServers' object"
    )
    return servers


def test_mcp_manifests_exist() -> None:
    manifests = _mcp_manifests()
    assert manifests, "no .mcp.json found under skills/ — the plugin MCP surface is missing"
    # Core and databases plugins must both ship one.
    rels = {str(m.relative_to(REPO_ROOT)) for m in manifests}
    assert "skills/core/.mcp.json" in rels, f"core .mcp.json missing; found {rels}"
    assert "skills/databases/.mcp.json" in rels, f"databases .mcp.json missing; found {rels}"


@pytest.mark.parametrize(
    "manifest", _mcp_manifests(), ids=[str(m.relative_to(REPO_ROOT)) for m in _mcp_manifests()]
)
def test_mcp_manifest_shape(manifest: Path) -> None:
    servers = _load_servers(manifest)
    for name, cfg in servers.items():
        assert isinstance(name, str) and name, f"{manifest}: empty server name"
        assert isinstance(cfg, dict), f"{manifest}:{name} config must be an object"
        # A bundled server is either a local command or a remote url server.
        assert "command" in cfg or "url" in cfg, (
            f"{manifest}:{name} must define 'command' or 'url'"
        )
        if "command" in cfg:
            assert isinstance(cfg["command"], str) and cfg["command"], (
                f"{manifest}:{name} 'command' must be a non-empty string"
            )
            args = cfg.get("args", [])
            assert isinstance(args, list), f"{manifest}:{name} 'args' must be a list"
            env = cfg.get("env", {})
            assert isinstance(env, dict), f"{manifest}:{name} 'env' must be an object"


@pytest.mark.parametrize(
    "manifest", _mcp_manifests(), ids=[str(m.relative_to(REPO_ROOT)) for m in _mcp_manifests()]
)
def test_every_server_is_documented(manifest: Path) -> None:
    assert MCP_SETUP_DOC.is_file(), f"missing MCP doc at {MCP_SETUP_DOC}"
    doc = MCP_SETUP_DOC.read_text(encoding="utf-8")
    servers = _load_servers(manifest)
    for name in servers:
        # Documented as a backtick-quoted token `name` somewhere in the setup doc.
        pattern = rf"`{re.escape(name)}`"
        assert re.search(pattern, doc), (
            f"server '{name}' in {manifest.relative_to(REPO_ROOT)} is not documented "
            f"in {MCP_SETUP_DOC.relative_to(REPO_ROOT)} (expected a `{name}` mention)"
        )


@pytest.mark.parametrize(
    "manifest", _mcp_manifests(), ids=[str(m.relative_to(REPO_ROOT)) for m in _mcp_manifests()]
)
def test_expected_academic_servers_present(manifest: Path) -> None:
    servers = set(_load_servers(manifest))
    missing = EXPECTED_SERVERS - servers
    assert not missing, (
        f"{manifest.relative_to(REPO_ROOT)} is missing bundled academic servers: {missing}"
    )


def test_core_and_databases_manifests_agree() -> None:
    core = _load_servers(SKILLS_DIR / "core" / ".mcp.json")
    db = _load_servers(SKILLS_DIR / "databases" / ".mcp.json")
    assert set(core) == set(db), (
        "core and databases .mcp.json must bundle the same server set; "
        f"core={set(core)} databases={set(db)}"
    )
