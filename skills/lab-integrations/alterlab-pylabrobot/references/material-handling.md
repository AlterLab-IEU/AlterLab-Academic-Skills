# Material Handling and Environmental Devices in PyLabRobot

Checked against pylabrobot 0.2.2 (2026-09). Each device is a front-end class plus a backend. Front ends that hold a plate (heater shakers, temperature controllers, thermocyclers) are also resources: assign a plate to them, or place them on a deck/carrier so the liquid handler can reach them. Use the chatterbox backends to simulate.

| Device family | Module | Front end | Hardware backends / factories | Simulation |
|---------------|--------|-----------|-------------------------------|------------|
| Heater shakers | `pylabrobot.heating_shaking` | `HeaterShaker` | `HamiltonHeaterShakerBackend` (+ `HamiltonHeaterShakerBox` or a STAR as interface), `inheco_thermoshake(...)`, `BioShake` | `HeaterShakerChatterboxBackend` |
| Temperature control | `pylabrobot.temperature_controlling` | `TemperatureController` | `OpentronsTemperatureModuleV2(...)`, `inheco_cpac_ultraflat(...)` | `TemperatureControllerChatterboxBackend` |
| Shakers | `pylabrobot.shaking` | `Shaker` | device specific | `ShakerChatterboxBackend` |
| Incubators / plate hotels | `pylabrobot.storage` | `Incubator` (Inheco incubator-shaker stacks: `pylabrobot.storage.inheco.IncubatorShakerStack`) | `CytomatBackend`, `SCILABackend` (Inheco SCILA), `InhecoIncubatorShakerStackBackend`, `ExperimentalLiconicBackend` | `IncubatorChatterboxBackend` |
| Centrifuges | `pylabrobot.centrifuge` | `Centrifuge`, `Loader` | `VSpinBackend` (Agilent VSpin), `Access2(...)` (VSpin + Access2 loader) | `CentrifugeChatterboxBackend` |
| Pumps | `pylabrobot.pumps` | `Pump`, `PumpArray` | `MasterflexBackend` (Cole-Parmer), `AgrowPumpArrayBackend` | `PumpChatterboxBackend`, `PumpArrayChatterboxBackend` |
| Thermocyclers | `pylabrobot.thermocycling` | `Thermocycler` | `OpentronsThermocyclerModuleV1/V2(...)`, `ATCBackend`, `ProflexBackend` | `ThermocyclerChatterboxBackend` |
| Plate sealers | `pylabrobot.sealing` | `Sealer` | `A4SBackend(port=...)` | — |

Older paths such as `pylabrobot.temperature_control`, `pylabrobot.incubation`, `pylabrobot.heating_shaking.hamilton`, and `pylabrobot.pumps.agrowtek` do not exist in 0.2.2; the classes `ColeParmerMasterflexBackend`, `InhecoThermoShakeBackend`, and `AgrowPumpArray` were renamed to the names in the table (`AgrowPumpArray` now raises an error pointing to `AgrowPumpArrayBackend`).

Install the connection extra for your hardware: `[usb]` (Hamilton heater-shaker box), `[hid]` (Inheco TEC control box), `[serial]` (Cytomat, Masterflex, BioShake, A4S, Opentrons temperature module over USB serial), `[ftdi]` (VSpin), `[modbus]` (Agrowtek pumps), `[opentrons]` (Opentrons modules through the robot's HTTP API), or `[all]`.

## Heater shakers and temperature controllers

`HeaterShaker` combines the `TemperatureController` and `Shaker` interfaces:

| Call | Effect |
|------|--------|
| `await hs.set_temperature(37)` | Set the target and return; cooling below the current temperature raises on devices without active cooling unless `passive=True` |
| `await hs.wait_for_temperature(timeout=300, tolerance=0.5)` | Block until within tolerance, or raise on timeout |
| `await hs.get_temperature()` | Current temperature |
| `await hs.deactivate()` | Stop heating/cooling |
| `await hs.lock_plate()` / `unlock_plate()` | Clamp or release the plate |
| `await hs.shake(speed=800, duration=None)` | Shake at `speed` rpm (locking the plate first when supported); with `duration` it waits that many seconds, then stops and unlocks; without it, it returns at once and shakes until `stop_shaking()` |
| `await hs.stop_shaking()` | Stop shaking |

```python
import asyncio

from pylabrobot.heating_shaking import HeaterShaker, HeaterShakerChatterboxBackend
from pylabrobot.resources import Coordinate, cor_96_wellplate_360uL_Fb


async def incubate():
    # Simulated unit; the size and child_location of a Hamilton heater shaker are
    # 146.2 x 103.6 x 74.11 mm with the plate at (10, 13, 74.24).
    hs = HeaterShaker(name="hs", size_x=146.2, size_y=103.6, size_z=74.11,
                      child_location=Coordinate(10, 13, 74.24),
                      backend=HeaterShakerChatterboxBackend())
    await hs.setup()
    try:
        hs.assign_child_resource(cor_96_wellplate_360uL_Fb(name="plate"))
        await hs.lock_plate()
        await hs.set_temperature(37)
        await hs.shake(speed=800, duration=2)  # a real assay would run minutes to hours
        await hs.deactivate()
        await hs.unlock_plate()
    finally:
        await hs.stop()


asyncio.run(incubate())
```

Chatterbox backends report the dummy temperature, so leave `wait_for_temperature` for hardware runs.

On hardware:

```python
from pylabrobot.heating_shaking import (
    HamiltonHeaterShakerBackend, HamiltonHeaterShakerBox, inheco_thermoshake,
)
from pylabrobot.temperature_controlling import (
    InhecoTECControlBox, OpentronsTemperatureModuleV2, inheco_cpac_ultraflat,
)

# Hamilton heater shaker on a USB control box (pass a STARBackend instead of the box
# when the shaker is wired to the STAR); index = position on the box
box = HamiltonHeaterShakerBox()
hhs_backend = HamiltonHeaterShakerBackend(index=0, interface=box)
hs = HeaterShaker(name="hs", size_x=146.2, size_y=103.6, size_z=74.11,
                  child_location=Coordinate(10, 13, 74.24), backend=hhs_backend)
await box.setup()  # the box first: the shaker backend talks through it
await hs.setup()

# Inheco ThermoShake and CPAC share one TEC control box
tec = InhecoTECControlBox()
thermoshake = inheco_thermoshake(name="thermoshake", control_box=tec, index=1)
cpac = inheco_cpac_ultraflat(name="cpac", control_box=tec, index=2)

# Opentrons Temperature Module GEN2 through an OT-2 (id from the robot) or a USB serial port
temp_module = OpentronsTemperatureModuleV2(name="temp", serial_port="/dev/ttyACM0")
```

Check your device manuals for the control-box setup order and indices; they are specific to your installation.

## Incubators and plate hotels

`Incubator(backend, name, size_x, size_y, size_z, racks, loading_tray_location)` models the storage racks so it can track which plate is where.

```python
from pylabrobot.resources import Coordinate
from pylabrobot.storage import CytomatBackend, Incubator
from pylabrobot.storage.cytomat.racks import cytomat_rack_9mm_51

incubator = Incubator(
    backend=CytomatBackend(model="C6000", port="/dev/ttyUSB0"),  # models: C6000, C6002, C2C_50, C2C_425, C2C_450_SHAKE, C5C
    name="cytomat", size_x=860, size_y=550, size_z=900,          # measure your unit
    racks=[cytomat_rack_9mm_51("rack_1")],
    loading_tray_location=Coordinate(0, 0, 0),                    # calibrate for your deck
)
await incubator.setup()
await incubator.set_temperature(37)
# put the plate on incubator.loading_tray first (robot arm, or
# incubator.loading_tray.assign_child_resource(plate) to record a manual placement)
await incubator.take_in_plate("smallest")                  # or "random", or a specific site
plate = await incubator.fetch_plate_to_loading_tray("assay_plate")
print(incubator.summary(), await incubator.get_temperature())
await incubator.stop()
```

Other calls: `open_door()`, `close_door()`, `start_shaking(frequency)`, `stop_shaking()`, `get_num_free_sites()`, `get_site_by_plate_name(name)`.

## Centrifuges

```python
from pylabrobot.centrifuge import Access2, VSpinBackend

vspin = VSpinBackend(device_id="VSPIN_FTDI_SERIAL")  # FTDI device id of the VSpin
centrifuge, loader = Access2(name="access2", device_id="ACCESS2_FTDI_SERIAL", vspin=vspin)
await centrifuge.setup()
await loader.setup()

# the plate sits on the Access2 stage (moved there by the robot arm, or tracked with
# loader.assign_child_resource(plate)); load() needs the door open and a bucket in position
await centrifuge.open_door()
await centrifuge.go_to_bucket1()
await loader.load()
await centrifuge.close_door()
await centrifuge.spin(g=1000, duration=300, acceleration=0.8)  # duration = seconds at speed
await centrifuge.open_door()
await centrifuge.go_to_bucket1()
await loader.unload()
```

Without the Access2 loader, build `Centrifuge(backend=VSpinBackend(...), name=..., size_x=..., size_y=..., size_z=...)` and use `open_door()`, `close_door()`, `lock_door()`, `unlock_door()`, `go_to_bucket1()` / `go_to_bucket2()`, and `spin(g, duration)`. Pass `acceleration` (0–1) explicitly: the VSpin backend defaults it, but the chatterbox backend requires it. Always balance the buckets.

## Pumps

```python
from pylabrobot.pumps import MasterflexBackend, Pump, PumpCalibration

pump = Pump(backend=MasterflexBackend(com_port="/dev/ttyUSB0"))
await pump.setup()
await pump.run_for_duration(speed=100, duration=10)  # speed in rpm (pump-specific units), duration in s
await pump.run_continuously(speed=50)
await pump.halt()
```

`pump_volume(speed, volume)` needs a `PumpCalibration` passed as `Pump(backend=..., calibration=...)`: measure delivered volume at fixed settings and build the calibration from those measurements (see the `PumpCalibration` class methods). Multi-channel peristaltic arrays use `PumpArray(backend=AgrowPumpArrayBackend(port="/dev/ttyUSB0", address=1))` with `use_channels=[...]` on each call.

## Thermocyclers

```python
from pylabrobot.thermocycling import OpentronsThermocyclerModuleV2

tc = OpentronsThermocyclerModuleV2(name="tc", opentrons_id="<module id from the OT-2>")
await tc.setup()
await tc.close_lid()
await tc.run_pcr_profile(
    denaturation_temp=[98], denaturation_time=10,
    annealing_temp=[60], annealing_time=30,
    extension_temp=[72], extension_time=30,
    num_cycles=30, block_max_volume=25, lid_temperature=[105],
    pre_denaturation_temp=[98], pre_denaturation_time=30,
    final_extension_temp=[72], final_extension_time=300,
    storage_temp=[4], storage_time=0,
)
await tc.wait_for_profile_completion()
await tc.open_lid()
```

Temperatures are lists (one per block zone). Lower-level calls: `set_block_temperature`, `set_lid_temperature`, `wait_for_block`, `wait_for_lid`, `deactivate_block`, `deactivate_lid`, `run_protocol(protocol, block_max_volume)`.

## Multi-device protocols

- Start slow steps (heating, incubator temperature) first and do liquid handling while they settle.
- Run independent devices concurrently with `asyncio.gather(...)`, but never let two devices move the same plate at once.
- Put every device's `stop()` in a `finally:` block (or an `AsyncExitStack`) so hardware is released after errors.
- Log each step with timestamps, temperatures, speeds, and durations for the protocol record.
