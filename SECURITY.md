# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in AlterLab Academic Skills, please report it responsibly.

**Report via:** [Open a GitHub issue](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills/issues) on this repository (use the "Security" label for sensitive reports).

Please include:

- Description of the vulnerability
- Steps to reproduce
- Affected skill(s) and file path(s)
- Potential impact assessment

## Response Timeline

- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 5 business days
- **Fix/Mitigation:** Based on severity

## Scope

Security concerns for this project include:

- **Prompt injection:** Skills that could be manipulated to execute unintended actions
- **Data exfiltration:** Skills that could leak sensitive information
- **Path traversal:** Skills with hardcoded or manipulable file paths
- **Credential exposure:** Skills that might expose API keys or tokens

## Skill Security Scanning

All pull requests that modify skills are scanned for potential security issues. We recommend:

- Never hardcode file paths, API keys, or credentials in skills
- Use environment variables for sensitive configuration
- Validate all external input referenced in skill instructions
- Follow the principle of least privilege for allowed tools metadata

## Trust Manifest

[`SECURITY_SCAN.md`](SECURITY_SCAN.md) is a **generated, CI-attested** manifest of the
shipped skill code. It enumerates the full outbound-host allowlist (all legitimate
scientific/academic APIs, user-keyed LLM backends, or documentation placeholders — no
telemetry) and attests, from a static scan, that the code contains **no shell-pipe, no
`os.system` / `shell=True`, no `eval`/`exec` on input, and no hardcoded secrets**.

It is regenerated with `python3 scripts/gen_security_scan.py` and enforced in CI:
`--check` fails the build if the manifest drifts from the code, and `--strict` fails if any
attestation is violated. So the manifest can never silently go stale or become untrue — it
is a verifiable signal you can check before installing, not a hand-maintained promise.

## Supported Versions

| Version | Supported |
|---------|-----------|
| v1.0.0 (Latest)  | Yes       |
