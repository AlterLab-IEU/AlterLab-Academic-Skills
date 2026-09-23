---
name: alterlab-ginkgo-cloud
description: Submits and manages protocols on Ginkgo Bioworks Cloud Lab (cloud.ginkgo.bio), a web-based interface for autonomous lab execution on Reconfigurable Automation Carts (RACs), covering protocol selection, input preparation, pricing, and ordering workflows. Use when running cell-free protein expression (validation or optimization), generating fluorescent pixel art, or interacting with Ginkgo Cloud Lab services. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: Requires a Ginkgo Cloud Lab account (cloud.ginkgo.bio); account creation or institutional access may be needed to submit and order protocols. Ordering is through the web interface; there is no documented public API.
metadata:
    skill-author: AlterLab
    version: "1.1.0"
    last_updated: "2026-09-23"
---

# Ginkgo Cloud Lab

## Overview

Ginkgo Cloud Lab (https://cloud.ginkgo.bio) provides remote access to Ginkgo Bioworks' autonomous lab infrastructure. Protocols are executed on Reconfigurable Automation Carts (RACs) -- modular units with robotic arms, maglev sample transport, and industrial-grade software spanning 70+ instruments.

The platform also includes **EstiMate**, an AI agent that accepts human-language protocol descriptions and returns feasibility assessments and pricing for custom workflows beyond the listed protocols.

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
