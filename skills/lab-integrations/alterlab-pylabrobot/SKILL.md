---
name: alterlab-pylabrobot
description: Programs lab automation with PyLabRobot, a vendor-agnostic async Python framework that drives Hamilton STAR/Vantage, Tecan EVO, and Opentrons OT-2 liquid handlers plus plate readers, heater shakers, incubators, centrifuges, pumps, scales, and thermocyclers, with a chatterbox simulator and browser visualizer. Use when writing or simulating liquid-handling protocols in Python, controlling several instrument types from one script, or porting a protocol between robot vendors. For Opentrons-only protocols written with the official Opentrons API, use alterlab-opentrons instead. Part of the AlterLab Academic Skills suite.
license: MIT
allowed-tools: Read Write Edit Bash(curl:*) Bash(python:*)
compatibility: "pylabrobot >=0.2 (current 0.2.2 as of 2026-09; Python >=3.9); install with uv pip install pylabrobot. The chatterbox backends simulate without hardware; real devices need the connection extra for their interface ([usb], [serial], [ftdi], [hid], [modbus], [opentrons], or [all])."
metadata:
    skill-author: AlterLab
    version: "1.2.0"
    last_updated: "2026-09-23"
---

# PyLabRobot

## Overview

PyLabRobot (PLR) is a hardware-agnostic Python SDK for lab automation. Every device is a front end (`LiquidHandler`, `PlateReader`, `HeaterShaker`, ...) plus a backend for a specific instrument, so the same protocol code runs on a simulator, a Hamilton STAR, or an Opentrons OT-2 by swapping one backend line. All device calls are `async` and must be awaited inside an event loop (`asyncio.run(main())`, or directly in a Jupyter cell).

## When to Use This Skill

- Writing or debugging a liquid-handling protocol in Python for Hamilton STAR/STARlet/Vantage, Tecan EVO, or Opentrons OT-2
- Simulating a protocol (chatterbox backend, tip/volume tracking, browser visualizer) before touching hardware
- Defining deck layouts: carriers, tip racks, plates, troughs, tubes, and custom labware
- Integrating plate readers, heater shakers, incubators, centrifuges, pumps, scales, or thermocyclers into one workflow
- Porting a protocol from one robot vendor to another

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Writing an Opentrons OT-2/Flex protocol with the official Opentrons Python API (`apiLevel`, `opentrons_simulate`) | `alterlab-opentrons` |
| Sending work to a remote cloud lab instead of running your own robot | `alterlab-ginkgo-cloud` |
| Ordering protein binding/expression assays from the Adaptyv Bio foundry | `alterlab-adaptyv` |
| Finding, writing, or publishing a human-readable protocol with a DOI | `alterlab-protocolsio` |

## Core Capabilities

| Area | What it covers | Reference |
|------|----------------|-----------|
| Liquid handling | `aspirate`, `dispense`, `transfer`, tips, multichannel moves, serial dilutions, error handling | `references/liquid-handling.md` |
| Resources | Decks, carriers, plates, tip racks, troughs, indexing, tracking, saving layouts, custom labware | `references/resources.md` |
| Hardware backends | STAR, Vantage, EVO, OT-2, chatterbox; switching backends | `references/hardware-backends.md` |
| Analytical equipment | Plate readers (CLARIOstar, BioTek, SpectraMax, Byonoy), scales | `references/analytical-equipment.md` |
| Material handling | Heater shakers, temperature controllers, incubators, centrifuges, pumps, thermocyclers | `references/material-handling.md` |
| Visualization | Browser visualizer, simulation-driven testing | `references/visualization.md` |

## Quick Start (simulation)

```python
import asyncio

from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend  # STARBackend() on a real STAR
from pylabrobot.resources import (
    PLT_CAR_L5AC_A00,                   # plate carrier (5 sites)
    STARLetDeck,
    TIP_CAR_480_A00,                    # tip carrier (5 sites)
    cor_96_wellplate_360uL_Fb,
    hamilton_96_tiprack_1000uL_filter,
    set_tip_tracking,
    set_volume_tracking,
)


async def main():
    set_tip_tracking(True)      # catch missing tips and over-aspiration in simulation
    set_volume_tracking(True)

    lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
    await lh.setup()
    try:
        # Labware goes into carrier sites; carriers go on deck rails.
        tip_car = TIP_CAR_480_A00(name="tip_carrier")
        tip_car[0] = tip_rack = hamilton_96_tiprack_1000uL_filter(name="tips_01")
        lh.deck.assign_child_resource(tip_car, rails=3)

        plt_car = PLT_CAR_L5AC_A00(name="plate_carrier")
        plt_car[0] = source = cor_96_wellplate_360uL_Fb(name="source")
        plt_car[1] = dest = cor_96_wellplate_360uL_Fb(name="dest")
        lh.deck.assign_child_resource(plt_car, rails=15)

        for well in source.get_all_items():
            well.tracker.set_liquids([(None, 300)])

        # 8-channel column copy: "A1:H1" is column 1 (8 wells), one tip per channel
        await lh.pick_up_tips(tip_rack["A1:H1"])
        await lh.aspirate(source["A1:H1"], vols=[100] * 8)
        await lh.dispense(dest["A1:H1"], vols=[100] * 8)
        await lh.discard_tips()         # to the deck's trash; return_tips() puts them back

        print(dest.get_well("A1").tracker.get_used_volume())  # 100.0
    finally:
        await lh.stop()


asyncio.run(main())
```

To run on hardware, replace the backend (`STARBackend()`, `VantageBackend()`, `EVOBackend()`, `OpentronsOT2Backend(host="<robot IP>")`) and the deck (`STARDeck()`, `VantageDeck(size=1.3)`, `EVO150Deck()`, `OTDeck()`); the protocol body stays the same apart from deck positions.

## API Rules That Prevent Most Errors

- **Indexing returns lists.** `plate["A1"]` is a one-element list; `plate["A1:H1"]` is column 1 and `plate["A1:A12"]` is row A. Use `plate.get_well("A1")` or `tip_rack.get_item("A1")` for a single object (for example to reach `.tracker`).
- **Volumes are lists.** `vols=[100]` for one channel, `vols=[100] * 8` for eight; per-channel options (`flow_rates`, `liquid_height`, `blow_out_air_volume`) are lists too.
- **Tips.** `pick_up_tips(spots)`, then `discard_tips()` (trash), `return_tips()` (back to the rack), or `drop_tips(spots)` (explicit spots — it has no default).
- **`transfer` is one-to-many.** `lh.transfer(source.get_well("A1"), dest["A1:H1"], target_vols=[50] * 8)` aspirates once and dispenses into each target with the channel-0 tip. `source_vol=` is the **total** volume, split across targets (equally or by `ratios`), not a per-target volume.
- **Labware names.** Use the current lower-case factories (`cor_96_wellplate_360uL_Fb`); capitalised legacy names such as `Cor_96_wellplate_360ul_Fb` warn and will be removed.
- **Always `stop()` in `finally:`** so USB/serial connections are released after an error.

## Common Workflows

### One-to-many dispense and a serial dilution

```python
# 50 uL of diluent into each of A2..A5 from one source well (single channel)
await lh.pick_up_tips(tip_rack["A2"])
await lh.transfer(source.get_well("H12"), dest["A2:A5"], target_vols=[50] * 4)
await lh.discard_tips()

# 2-fold dilution along row A (A1 -> A5): move 50 uL to the next well and mix
await lh.pick_up_tips(tip_rack["A3"])
for col in range(1, 5):
    await lh.aspirate(dest[f"A{col}"], vols=[50])
    await lh.dispense(dest[f"A{col + 1}"], vols=[50])
    for _ in range(3):  # mix
        await lh.aspirate(dest[f"A{col + 1}"], vols=[40])
        await lh.dispense(dest[f"A{col + 1}"], vols=[40])
await lh.discard_tips()
```

### Reading a plate

```python
from pylabrobot.plate_reading import CLARIOstarBackend, PlateReader

reader = PlateReader(name="clariostar", size_x=0, size_y=0, size_z=0,
                     backend=CLARIOstarBackend())   # needs pylabrobot[ftdi]
await reader.setup()
await reader.open()
reader.assign_child_resource(dest)                   # or move the plate there with the robot's gripper
await reader.close()
result = await reader.read_absorbance(wavelength=450, use_new_return_type=True)
od450 = result[0]["data"]                            # 8 x 12 nested list
await reader.stop()
```

`PlateReader` has no temperature method; readers that support heating expose it on the backend (for example `await reader.backend.set_temperature(37)` on BioTek and Molecular Devices backends). See `references/analytical-equipment.md` for other readers and for scales.

## Best Practices

1. **Simulate first.** Run the whole protocol on `LiquidHandlerChatterboxBackend` with tip and volume tracking on, and watch it in the `Visualizer`, before the first hardware run.
2. **Dry-run on hardware.** Do a first physical run with water or without liquid, at reduced volumes, and keep a hand near the stop button.
3. **Keep layouts in files.** Save the deck with `lh.deck.save("deck.json")` and commit it with the protocol; record the pylabrobot version.
4. **Check labware definitions.** Verify geometry for custom or rarely used labware before trusting aspiration heights.
5. **Start slow devices early.** Heating and incubator set points take minutes; do liquid handling while they settle.
6. **Official docs.** https://docs.pylabrobot.org (user guide and API), https://github.com/PyLabRobot/pylabrobot, forum https://discuss.pylabrobot.org.

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| `TypeError: Resources must be Containers, got [[Well(...)]]` | A list was passed where one well is expected (`transfer` source); use `plate.get_well("A1")` |
| `TypeError: drop_tips() missing ... 'tip_spots'` | Use `discard_tips()` or pass explicit spots |
| `NoTipError` / `HasTipError` with tracking on | The protocol reuses a tip spot or picks up while holding tips; check tip bookkeeping |
| `RuntimeError: ... is not installed. Install with: pip install pylabrobot[...]` | Install the connection extra named in the message |
| `ImportError` for `pylabrobot.temperature_control`, `pylabrobot.incubation`, `Trough_100ml` | Outdated names; see `references/material-handling.md` and `references/resources.md` for the 0.2.2 modules and labware |

Part of the AlterLab Academic Skills suite.
