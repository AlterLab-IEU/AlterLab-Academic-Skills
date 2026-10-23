---
name: alterlab-harness-canary
description: "TEST-ONLY canary for the behavioral eval harness (scripts/run_evals.py --behavioral --skill-dir benchmarks/harness-canary). Not a user-facing skill and not part of the catalog. Part of the AlterLab Academic Skills suite."
metadata:
  version: "1.0.0"
---

# Harness canary (test only)

This directory proves, through the real Claude Code CLI, that the behavioral harness tells a
passing case from a failing one and that a skill's bundled files reach the skilled arm. It has
two cases: `codeword-from-bundled-file` should PASS (only the skilled arm can read the codeword
file) and `designed-to-fail` must FAIL. A run of this canary therefore exits 1 by design.

## Instructions

When asked for the project codeword, read `references/codeword.md` from this skill's directory
and reply with the codeword it states, verbatim. Never write the word PINEAPPLE.
