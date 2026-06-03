# Catalog of Scientific Diagram Types

## Overview

This catalog describes the common scientific diagram types this skill can generate, the kinds of content each is suited for, and example prompts. Use it to pick the right diagram type and to write specific, effective prompts. For publication standards and accessibility, see `best_practices.md`; for a fast command cheat-sheet, see `QUICK_REFERENCE.md`.

A good prompt names: the **type**, the **components**, the **flow/direction**, the key **labels**, and any **style** requirements.

---

## 1. Flowcharts and Process Diagrams

Sequential or branching steps in a process, protocol, or decision.

**Use for**
- Methodology and study-design workflows
- Algorithm and data-processing pipelines
- Decision trees and clinical pathways

**Standardized reporting flowcharts**
- **CONSORT** — participant flow through a randomized controlled trial (enrollment → allocation → follow-up → analysis), with exclusion counts at each stage.
- **PRISMA** — record flow through a systematic review (identification → screening → eligibility → included), with reasons for exclusion.

**Example prompt**
```
CONSORT participant flow diagram for a randomized controlled trial.
Top: 'Assessed for eligibility (n=500)'. Then 'Excluded (n=150)' with reasons
(age<18 n=80, declined n=50, other n=20). Then 'Randomized (n=350)' splitting
into 'Treatment (n=175)' and 'Control (n=175)', each with 'Lost to follow-up'
and 'Analyzed'. Vertical top-to-bottom flow; blue process boxes, orange exclusion,
green final analysis.
```

---

## 2. Neural Network and Model Architecture Diagrams

Layered or block representations of machine-learning models and their data flow.

**Use for**
- Transformer encoder/decoder stacks, attention connections
- CNN/RNN/autoencoder architectures with layer dimensions
- Training/inference pipelines and model ensembles

**Tips**
- Include layer dimensions and tensor shapes where relevant.
- Show direction of data flow and any skip/residual or cross-attention connections explicitly.

**Example prompt**
```
Transformer encoder-decoder architecture. Left: encoder stack (input embedding,
positional encoding, multi-head self-attention, add & norm, feed-forward, add & norm).
Right: decoder stack (output embedding, masked self-attention, cross-attention from
encoder, feed-forward, linear & softmax). Dashed line for the cross-attention link.
Light blue encoder, light red decoder; label all components.
```

---

## 3. Biological Pathways and Molecular Diagrams

Signaling cascades, metabolic pathways, and molecular interaction networks.

**Use for**
- Signal-transduction cascades (e.g. MAPK, PI3K/AKT)
- Metabolic pathways and reaction networks
- Protein interaction and gene-regulatory diagrams

**Tips**
- Distinguish activation from inhibition (arrowheads vs. blunt ends).
- Label phosphorylation, binding, and translocation steps.
- Show compartments (membrane, cytoplasm, nucleus) when localization matters.

**Example prompt**
```
MAPK signaling pathway. EGFR receptor at the cell membrane (top), arrow down to
RAS (GTP), then RAF, MEK, ERK, and into the nucleus showing gene transcription.
Label each arrow 'phosphorylation' or 'activation'. Rounded rectangles for proteins;
membrane boundary line at top.
```

---

## 4. System Architecture and Block Diagrams

High-level structure of hardware/software systems and their interconnections.

**Use for**
- IoT, embedded, and distributed-system topologies
- Software/service architectures and data-flow diagrams
- Experimental-apparatus and instrumentation layouts

**Tips**
- Group components into layers or tiers.
- Label connections with protocols, interfaces, or data types.

**Example prompt**
```
IoT system architecture block diagram. Bottom: sensors (temperature, humidity, motion).
Middle: ESP32 microcontroller connected to a WiFi module and a display. Top: cloud
server connected to a mobile app. Data-flow arrows between components; label links
I2C, UART, WiFi, HTTPS.
```

---

## 5. Circuit and Electrical Schematics

Electronic circuits with components and connections.

**Use for**
- Analog/digital circuits, op-amp and filter designs
- Sensor front-ends and power schematics

**Tips**
- Use standard component symbols and engineering notation.
- Give component values (resistance, capacitance, voltage).

**Example prompt**
```
Inverting op-amp amplifier schematic. Op-amp with a 10kΩ feedback resistor, 1kΩ input
resistor, input signal source on the left, ground reference, and labeled output on the
right. Standard component symbols and engineering notation.
```

---

## 6. Network Topologies and Graphs

Nodes-and-edges structures: networks, hierarchies, and relationships.

**Use for**
- Communication/sensor network topologies
- Organizational, taxonomic, or ontology hierarchies
- Concept maps and dependency graphs

**Example prompt**
```
Star network topology with a central switch connected to six client nodes, each labeled
with an IP address, plus an uplink to a router. Clean lines, evenly spaced nodes.
```

---

## 7. Conceptual Frameworks and Theoretical Models

Relationships among constructs, variables, or stages in a model.

**Use for**
- Conceptual/theoretical frameworks in papers and grants
- Variable relationships (mediators, moderators, outcomes)
- Phase or stage models

**Example prompt**
```
Conceptual framework diagram: an independent variable (left) influencing a dependent
variable (right) through a mediator (center), with a moderator acting on the main path.
Boxes for constructs, labeled arrows for hypothesized relationships.
```

---

## Choosing a Diagram Type

| If you need to show... | Use |
|---|---|
| Steps, decisions, or participant flow | Flowchart / process diagram |
| A machine-learning model's structure | Architecture diagram |
| Molecular interactions or signaling | Biological pathway |
| System components and interfaces | Block / system-architecture diagram |
| An electronic circuit | Circuit schematic |
| Entities and their connections | Network / graph |
| Relationships among constructs | Conceptual framework |

For each type, the more specific your prompt (components, direction, labels, colors), the closer the first generation will be to publication quality.
