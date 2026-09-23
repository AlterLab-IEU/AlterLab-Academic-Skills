# Analytical Equipment in PyLabRobot

Checked against pylabrobot 0.2.2 (2026-09). Every device follows the same pattern as the liquid handler: a front end (`PlateReader`, `Scale`) plus a backend for the specific instrument, `await device.setup()` before use and `await device.stop()` at the end. Swap the backend for its chatterbox (simulation) twin to test without hardware.

## Plate readers

### Supported backends (all importable from `pylabrobot.plate_reading`)

| Instrument | Backend |
|------------|---------|
| BMG Labtech CLARIOstar / CLARIOstar Plus | `CLARIOstarBackend(device_id=None)` |
| Agilent BioTek Synergy H1 | `SynergyH1Backend()` |
| Agilent BioTek Cytation (plate reading + imaging) | `CytationBackend()` (`Cytation5Backend` is a deprecated alias) |
| Molecular Devices SpectraMax M5, 384 Plus, Gemini EM | `MolecularDevicesSpectraMaxM5Backend(port=...)`, `MolecularDevicesSpectraMax384PlusBackend(port=...)`, `MolecularDevicesSpectraMaxGeminiEMBackend(port=...)` |
| Byonoy Absorbance 96 / Luminescence 96 Automate | `ByonoyAbsorbance96AutomateBackend()`, `ByonoyLuminescence96AutomateBackend()` |
| Tecan Infinite 200 Pro, Spark 20M | `ExperimentalTecanInfinite200ProBackend`, `ExperimentalSparkBackend` (experimental) |
| Simulation | `PlateReaderChatterboxBackend()` |

The old import path `pylabrobot.plate_reading.clario_star_backend` still works in 0.2.2 but emits a deprecation warning; import from `pylabrobot.plate_reading` instead.

Hardware backends need the extra for their connection: `uv pip install "pylabrobot[ftdi]"` for the CLARIOstar and BioTek readers, `[serial]` for Molecular Devices, `[hid]` for Byonoy, `[usb]` for the Tecan readers (`[all]` installs every extra). Without it, constructing the backend raises an error naming the missing extra.

### Reading a plate

Reads act on the plate that is assigned to the reader, so assign the plate (or move it there with a robotic arm) before reading:

```python
import asyncio

from pylabrobot.plate_reading import PlateReader, PlateReaderChatterboxBackend
from pylabrobot.resources import cor_96_wellplate_360uL_Fb


async def main():
    # Use CLARIOstarBackend(), SynergyH1Backend(), ... on real hardware.
    reader = PlateReader(name="reader", size_x=0, size_y=0, size_z=0,
                         backend=PlateReaderChatterboxBackend())
    await reader.setup()
    try:
        await reader.open()
        plate = cor_96_wellplate_360uL_Fb(name="assay_plate")
        reader.assign_child_resource(plate)  # a plate must be in the reader before reading
        await reader.close()

        absorbance = await reader.read_absorbance(wavelength=450, use_new_return_type=True)
        luminescence = await reader.read_luminescence(focal_height=13.0, use_new_return_type=True)
        fluorescence = await reader.read_fluorescence(
            excitation_wavelength=485, emission_wavelength=528, focal_height=7.5,
            use_new_return_type=True,
        )
        od450 = absorbance[0]["data"]  # 8 x 12 nested list for a 96-well plate
        print(len(od450), len(od450[0]), luminescence[0]["data"][0][0], fluorescence[0]["data"][0][0])
    finally:
        await reader.stop()


asyncio.run(main())
```

- `size_x/size_y/size_z` are the reader's footprint in millimetres; they only matter when the reader sits on a deck or is reached by an arm.
- `use_new_return_type=True` returns a list of dictionaries (one per measurement) with `wavelength`, `time`, `temperature`, and `data`; without it 0.2.2 logs a warning and returns only the first `data` grid. Set it now so code keeps working when the default changes.
- Pass `wells=[...]` to read a subset of wells.
- Focal heights and wavelength ranges are instrument specific; check the backend (for BioTek: `backend.focal_height_range`, `backend.abs_wavelength_range`).

```python
import pandas as pd

rows = "ABCDEFGH"
df = pd.DataFrame(od450, index=list(rows), columns=range(1, 13))
```

### Temperature control in the reader

`PlateReader` itself has no temperature method. Readers that support it expose it on the backend:

```python
# BioTek (Synergy H1, Cytation): check support first
if reader.backend.supports_heating:
    await reader.backend.set_temperature(37)
    print(await reader.backend.get_current_temperature())

# Molecular Devices SpectraMax
await reader.backend.set_temperature(37)
```

Heating takes minutes; start it early and wait for the reading to stabilise before measuring. Backend methods are instrument specific, so check the backend class before relying on them in a shared protocol.

## Scales

The Mettler Toledo WXS205SDU is supported through `MettlerToledoWXS205SDUBackend` (serial; needs `pylabrobot[serial]`). The older `MettlerToledoWXS205SDU` class now raises an error telling you to use the backend:

```python
from pylabrobot.scales import MettlerToledoWXS205SDUBackend, Scale, ScaleChatterboxBackend

backend = ScaleChatterboxBackend(dummy_weight=0.0)  # on hardware: MettlerToledoWXS205SDUBackend(port="/dev/ttyUSB0")
scale = Scale(name="scale", size_x=0, size_y=0, size_z=0, backend=backend)
await scale.setup()
await scale.zero()                 # zero the empty pan
await scale.tare()                 # tare with the vessel on the pan
grams = await scale.read_weight()  # get_weight() is deprecated
await scale.stop()
```

### Gravimetric check of a dispense

```python
water_density = 0.998  # g/mL at about 20 °C
await scale.tare()
await lh.aspirate(reservoir["A1"], vols=[200])
await lh.dispense(vessel_on_scale, vols=[200])
measured_ul = await scale.read_weight() / water_density * 1000
print(f"dispensed {measured_ul:.1f} uL (target 200 uL)")
```

Place the vessel on a site the pipette can reach; weigh several replicates and report mean and CV rather than a single value.

## Combining a liquid handler and a reader

A typical assay loop: dispense with the liquid handler, move the plate into the reader (manually, or with the robot's gripper via `lh.move_plate(plate, reader)` when the reader is modelled on the deck), read, and save the data with the plate name and timestamp.

```python
import datetime as dt
import json

result = await reader.read_absorbance(wavelength=600, use_new_return_type=True)
record = {"plate": plate.name, "read_at": dt.datetime.now().isoformat(), "result": result}
with open(f"{plate.name}_od600.json", "w") as fh:
    json.dump(record, fh)
```

For kinetic reads, loop over reads with `asyncio.sleep` between them, or use the instrument's own kinetic mode through backend-specific arguments (for example the Molecular Devices `KineticSettings`).

## Good practice

- Develop against the chatterbox backends, then switch one line to the hardware backend.
- Always `stop()` devices in a `finally:` block so serial/USB connections are released after errors.
- Record instrument, backend, pylabrobot version, wavelengths, focal height, and temperature with every data file.
- Blank-correct absorbance with buffer-only wells on the same plate.
