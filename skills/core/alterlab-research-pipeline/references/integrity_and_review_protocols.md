# Integrity & Two-Stage Review Protocols (v2.0) — Full Detail

Phase-by-phase execution steps for the mandatory integrity gates (Stage 2.5, 4.5) and the two-stage peer review (Stage 3, 3'), including the Socratic revision-coaching transitions summarized in SKILL.md.

## Integrity Review Protocol (Added in v2.0)

### Stage 2.5: First Integrity Check (Pre-Review Integrity)

**Trigger**: After Stage 2 (WRITE) completion, before Stage 3 (REVIEW)
**Purpose**: Ensure all references and data are not fabricated or erroneous before submission for review

```
Execution steps:
1. integrity_verification_agent executes Mode 1 (initial verification) on the paper
2. Verification scope:
   - Phase A: 100% reference existence + bibliographic accuracy + ghost citations
   - Phase B: >= 30% citation context spot-check
   - Phase C: 100% statistical data verification
   - Phase D: >= 30% originality spot-check + self-plagiarism check
   - Phase E: 30% claim verification spot-check (minimum 10 claims)
3. Result handling:
   - PASS -> checkpoint -> Stage 3
   - FAIL -> produce correction list -> fix item by item -> re-verify corrected items
   - PASS after corrections -> checkpoint -> Stage 3
   - Still FAIL after 3 rounds -> notify user, list unverifiable items
```

### Stage 4.5: Final Integrity Check (Post-Revision Final Check)

**Trigger**: After Stage 4' (RE-REVISE) or Stage 3' (RE-REVIEW, Accept) completion, before Stage 5 (FINALIZE)
**Purpose**: Confirm the revised paper is 100% correct and ready for publication

```
Execution steps:
1. integrity_verification_agent executes Mode 2 (final verification) on the revised draft
2. Verification scope:
   - Phase A: 100% reference verification (including those added during revision)
   - Phase B: 100% citation context verification (not spot-check, full check)
   - Phase C: 100% statistical data verification
   - Phase D: >= 50% originality spot-check (100% for newly added/modified paragraphs)
   - Phase E: 100% claim verification (zero MAJOR_DISTORTION + zero UNVERIFIABLE required)
3. Special check: Compare with Stage 2.5 results to confirm all previous issues are resolved
4. Result handling:
   - PASS (zero issues) -> checkpoint -> Stage 5
   - FAIL -> fix -> re-verify -> PASS -> Stage 5
5. **Must PASS with zero issues to proceed to Stage 5**
```

## Two-Stage Review Protocol (Added in v2.0)

### Stage 3: First Review (Full Review)

- **Input**: Paper that passed integrity check
- **Review team**: EIC + R1 (methodology) + R2 (domain) + R3 (interdisciplinary) + Devil's Advocate
- **Output**: 5 review reports + Editorial Decision + Revision Roadmap + Socratic Revision Coaching
- **Decision branches**: Accept -> Stage 4.5 / Minor|Major -> Revision Coaching -> Stage 4 / Reject -> Stage 2 or end

See `alterlab-paper-reviewer/SKILL.md` for review process details.

### Stage 3 -> 4 Transition: Revision Coaching

EIC uses Socratic dialogue to guide the user in understanding review comments and planning revision strategy (max 8 rounds). User can say "just fix it for me" to skip.

### Stage 3': Second Review (Verification Review)

- **Input**: Revised draft + Response to Reviewers + original Revision Roadmap
- **Mode**: `alterlab-paper-reviewer` re-review mode
- **Output**: Revision response comparison table + new issues list + new Editorial Decision
- **Decision branches**: Accept|Minor -> Stage 4.5 / Major -> Residual Coaching -> Stage 4'

See `alterlab-paper-reviewer/SKILL.md` Re-Review Mode for verification review process.

### Stage 3' -> 4' Transition: Residual Coaching

EIC guides the user in understanding residual issues and making trade-offs (max 5 rounds). User can say "just fix it" to skip.
