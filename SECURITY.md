# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in AlterLab Academic Skills, please report it responsibly.

**Email:** security@alterlab.dev

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
- Follow the principle of least privilege for `allowed-tools` metadata

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
