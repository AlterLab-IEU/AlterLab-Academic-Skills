---
name: alterlab-ginkgo-cloud
description: Prepares and validates Ginkgo Bioworks Cloud Lab orders with no account — picks the right protocol (cell-free protein expression validation/optimization, fluorescent pixel art, and the newer catalog), validates the inputs offline (DNA length/format for CFPS, image-to-7-strain-palette mapping for pixel art), and assembles the sample counts, pricing and Additional Details into a ready-to-order package. Placing the order runs through the cloud.ginkgo.bio web interface (there is no public ordering API) with the user's own account. Use when running cell-free protein expression (validation or optimization), generating fluorescent pixel art, preparing or pricing a Ginkgo Cloud Lab order, or interacting with Ginkgo Cloud Lab services. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: "No API key required to choose a protocol, validate its inputs offline (scripts/check_cfps_input.py for CFPS DNA) and assemble a priced, ready-to-order package. Optional: a Ginkgo Cloud Lab account (cloud.ginkgo.bio) to place the order through the web interface — there is no documented public ordering API, so submission is always done in the UI."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-10-22"
---

# Ginkgo Cloud Lab

## Overview

Ginkgo Cloud Lab (https://cloud.ginkgo.bio) provides remote access to Ginkgo Bioworks' autonomous lab infrastructure. Protocols are executed on Reconfigurable Automation Carts (RACs) -- modular units with robotic arms, maglev sample transport, and industrial-grade software spanning 70+ instruments.

The platform also includes **EstiMate**, an AI agent that accepts human-language protocol descriptions and returns feasibility assessments and pricing for custom workflows beyond the listed protocols.

## Keyless Path (default — no Ginkgo account)

Ginkgo Cloud Lab has no public ordering API; orders are placed in the web UI. Everything up to that point is done with no account:

1. **Choose the protocol** for the user's goal from the catalog below (go/no-go expression -> CFPS Validation; a hard-to-express or membrane protein -> CFPS Optimization; living artwork -> Fluorescent Pixel Art; anything else -> EstiMate).
2. **Validate the inputs offline.** For cell-free expression, `python3 scripts/check_cfps_input.py constructs.fasta` checks each construct against the protocol limits (linear DNA, up to 1800 bp, ACGT/IUPAC only), flags over-length or non-DNA sequences, and prints the sample count and estimated cost. For pixel art, map the image's colours to the 7-strain fluorescent palette and confirm it fits the Echo 1536 (32x48) layout. No account is needed for any of this.
3. **Assemble the order package** — protocol, number of samples/proteins and replicates, uploaded input files, and the free-text Additional Details — with the price and turnaround read from the catalog (confirm on the live protocol page).
4. **Hand over the order step.** Placing and paying for the order is done by the user in the cloud.ginkgo.bio web interface; this skill does not and cannot submit it. Confirm current prices/turnaround on the protocol page before quoting, and follow the biosafety/sequence-sharing check below before any submission.

## When to Use This Skill

- Choosing and ordering a listed Cloud Lab protocol (cell-free expression validation or optimization, fluorescent pixel art, and the newer catalog entries below)
- Preparing inputs (DNA sequence files, pixel-art designs) and understanding outputs, pricing, and turnaround
- Getting a feasibility/pricing assessment for a custom protocol through EstiMate

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Submitting designed proteins to the Adaptyv Bio Foundry for binding/expression/stability assays | `alterlab-adaptyv` |
| Writing a protocol for your own Opentrons OT-2/Flex robot | `alterlab-opentrons` |
| Scripting your own multi-vendor liquid handlers (Hamilton, Tecan) | `alterlab-pylabrobot` |
| Publishing or finding a written protocol with a DOI | `alterlab-protocolsio` |

**Hand-off rule.** When the request matches a row above, open your answer by naming that skill by its exact id (for example `alterlab-adaptyv`) and saying in one line why it fits better, then stop applying this skill's procedure. Name it even when you also need to ask for missing input. If only part of the request is out of scope, name the skill for that part and do only the in-scope part. A brief general pointer is fine; the named skill does the work.

## Available Protocols

Prices and turnaround below are as listed on cloud.ginkgo.bio on 2026-09-23; they change, so confirm on the protocol page before quoting them.

### 1. Cell Free Protein Expression Validation

Rapid go/no-go expression screening using reconstituted E. coli CFPS. Submit a linear DNA sequence (up to 1800 bp; .fasta, .csv, .xlsx, .txt, .pdf, or .zip) and receive expression confirmation, baseline titer (mg/L), and initial purity with virtual gel images.

- **Price:** $39/sample | **Turnaround:** up to 10 days | **Status:** Certified
- **Details:** See [references/cell-free-protein-expression-validation.md](references/cell-free-protein-expression-validation.md)

### 2. Cell Free Protein Expression Optimization

DoE-based optimization across up to 24 conditions per protein (lysates, temperatures, chaperones, disulfide enhancers, cofactors). Designed for difficult-to-express and membrane proteins.

- **Price:** $199/sample | **Turnaround:** up to 11 days | **Status:** Certified
- **Details:** See [references/cell-free-protein-expression-optimization.md](references/cell-free-protein-expression-optimization.md)

### 3. Fluorescent Pixel Art Generation

Turn a design made in the Design Tool (upload an image or paint freehand) into fluorescent bacterial artwork: colors are mapped to a 7-strain fluorescent E. coli palette and printed by acoustic dispensing on an Echo 1536 layout (32×48 dots; a 6144 layout is announced as coming soon). Delivered as high-res UV photographs (TIFF/JPEG).

- **Price:** $25/plate | **Turnaround:** up to 7 days | **Status:** Beta
- **Details:** See [references/fluorescent-pixel-art-generation.md](references/fluorescent-pixel-art-generation.md)

### Newer catalog entries

The catalog has grown beyond the three protocols above. As rendered on 2026-09-23 it also listed IVT mRNA/circRNA qPCR; cell-free and E. coli expression with His-/Strep-tag purification and A280 or LabChip readouts (including minibinder variants); HiBiT luminescence expression readouts; Pichia expression (LabChip); cell-free thermal shift; Echo-MS; SPR kinetics (beta); and plate-reader method onboarding. Open each protocol page for its inputs, price, and turnaround — this skill has no detailed reference for them yet.

## General Ordering Workflow

1. Select a protocol at https://cloud.ginkgo.bio/protocols
2. Configure parameters (number of samples/proteins, replicates, plates)
3. Upload input files (sequence files for protein protocols; the Design Tool for pixel art)
4. Add any special requirements in the Additional Details field
5. Submit and receive a feasibility report and price quote

For protocols not listed above, use the **EstiMate** chat to describe a custom protocol in plain language and receive compatibility assessment and pricing.

Before submitting sequences, check your institution's rules on sharing unpublished or controlled sequences with an external provider, and follow biosafety review requirements for the constructs involved.

## Authentication

Access Ginkgo Cloud Lab at https://cloud.ginkgo.bio. Account creation or institutional access may be required. Contact Ginkgo at cloud@ginkgo.bio for access questions.

## Key Infrastructure

- **RACs (Reconfigurable Automation Carts):** Modular robotic units with high-precision arms and maglev transport
- **Catalyst Software:** Protocol orchestration, scheduling, parameterization, and real-time monitoring
- **70+ integrated instruments:** Sample prep, liquid handling, analytical readouts, storage, incubation
- **Nebula:** Ginkgo's autonomous lab facility in Boston, MA

Part of the AlterLab Academic Skills suite.
