# Resource Management in PyLabRobot

Checked against pylabrobot 0.2.2 (2026-09). Every snippet below runs on the chatterbox backend.

## The resource tree

Everything on a robot is a `Resource` with a `name` (unique on the deck), a size in millimetres (`size_x`, `size_y`, `size_z`), and a `location` relative to its parent. Resources form a tree: deck → carriers → plates/tip racks/troughs → wells/tip spots. Names must be unique across the whole deck.

Coordinates are right-handed: x increases to the right, y toward the back, z upward, with the origin at the front-left-bottom corner of the parent.

### Labware definitions

`pylabrobot.resources` ships vendor labware as factory functions named `<vendor>_<count>_<kind>_<volume>_<bottom>`, for example `cor_96_wellplate_360uL_Fb` (Corning 96-well, 360 µL, flat bottom), `hamilton_96_tiprack_1000uL_filter`, `hamilton_1_trough_200mL_Vb`, `eppendorf_tube_1500uL_Vb`. Older capitalised names such as `Cor_96_wellplate_360ul_Fb` still exist in 0.2.2 but warn that they will be removed; use the lower-case names. Carriers keep Hamilton catalogue names (`TIP_CAR_480_A00`, `PLT_CAR_L5AC_A00`, `Trough_CAR_4R200_A00`, `Tube_CAR_24_A00`).

Search for a definition before writing your own:

```python
import pylabrobot.resources as res

print([n for n in dir(res) if "96_wellplate" in n and n[0].islower()])  # current (lower-case) names
```

## Plates and wells

```python
from pylabrobot.resources import cor_96_wellplate_360uL_Fb

plate = cor_96_wellplate_360uL_Fb(name="sample_plate")

a1 = plate.get_well("A1")          # one Well object
column_1 = plate["A1:H1"]          # list of 8 wells: A1, B1, ..., H1
row_a = plate["A1:A12"]            # list of 12 wells: A1, A2, ..., A12
block = plate["A1:B2"]             # A1, A2, B1, B2
some = plate.get_wells(["A1", "C3"])
every_well = plate.get_all_items()
print(plate.num_items_x, plate.num_items_y, a1.max_volume)
```

`plate["A1"]` returns a **list** containing one well. Liquid-handling calls such as `aspirate` and `dispense` take lists, so `plate["A1"]` works there, but calls that take a single well (`lh.transfer(source, ...)`) or attribute access (`.tracker`) need `plate.get_well("A1")`.

## Tip racks, carriers, and troughs

On Hamilton decks, labware sits in carrier **sites**, and carriers go on deck **rails**:

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources import (
    PLT_CAR_L5AC_A00,
    STARLetDeck,
    TIP_CAR_480_A00,
    Trough_CAR_4R200_A00,
    cor_96_wellplate_360uL_Fb,
    hamilton_1_trough_200mL_Vb,
    hamilton_96_tiprack_1000uL_filter,
)

lh = LiquidHandler(backend=LiquidHandlerChatterboxBackend(), deck=STARLetDeck())
await lh.setup()

tip_car = TIP_CAR_480_A00(name="tip_carrier")                 # 5 tip-rack sites
tip_car[0] = tip_rack = hamilton_96_tiprack_1000uL_filter(name="tips_01")
lh.deck.assign_child_resource(tip_car, rails=1)

trough_car = Trough_CAR_4R200_A00(name="trough_carrier")      # 4 trough sites
trough_car[0] = buffer = hamilton_1_trough_200mL_Vb(name="buffer")
lh.deck.assign_child_resource(trough_car, rails=8)

plt_car = PLT_CAR_L5AC_A00(name="plate_carrier")              # 5 plate sites
plt_car[0] = source = cor_96_wellplate_360uL_Fb(name="source")
plt_car[1] = dest = cor_96_wellplate_360uL_Fb(name="dest")
lh.deck.assign_child_resource(plt_car, rails=15)

print(lh.deck.summary())
```

Index the rack or plate, never the carrier: `tip_rack["A1:H1"]`, not `tip_car["A1:H1"]`. Rails that overlap an existing carrier raise an error, which catches layout mistakes before a run.

Tubes work the same way: `Tube_CAR_24_A00(name=...)` holds 24 tubes such as `eppendorf_tube_1500uL_Vb(name=...)`.

### Other decks

```python
from pylabrobot.resources import EVO150Deck, OTDeck, STARDeck, VantageDeck, opentrons_96_tiprack_300ul

ot_deck = OTDeck()                                            # Opentrons OT-2: numbered slots 1-11
ot_deck.assign_child_at_slot(opentrons_96_tiprack_300ul(name="ot_tips"), slot=1)

star = STARDeck()                  # full-size STAR (STARLetDeck is the smaller STARlet)
vantage = VantageDeck(size=1.3)    # Hamilton Vantage, 1.3 or 2.0 m
evo = EVO150Deck()                 # Tecan EVO 150 (also EVO100Deck, EVO200Deck)
```

Any resource can also be placed at an explicit position with `deck.assign_child_resource(resource, location=Coordinate(x, y, z))`. Remove one with `deck.unassign_child_resource(resource)`.

### Locations

```python
from pylabrobot.resources import Coordinate

print(source.get_absolute_location())                # relative to the deck origin
print(source.get_well("A1").get_location_wrt(lh.deck))
print(source.location, source.get_size_x(), source.get_size_y(), source.get_size_z())
```

Sizes are read with `get_size_x()` / `get_size_y()` / `get_size_z()` (these account for rotation).

## Tip and volume tracking

Tracking lets PyLabRobot catch mistakes in simulation: picking up a tip that is not there, aspirating more than a well holds, or dispensing more than a tip contains.

```python
from pylabrobot.resources import set_tip_tracking, set_volume_tracking
from pylabrobot.resources.liquid import Liquid

set_tip_tracking(True)       # global switches, checked on every liquid-handling call
set_volume_tracking(True)

tracked_tips = hamilton_96_tiprack_1000uL_filter(name="tracked_tips")
tip_car[1] = tracked_tips
tracked_plate = cor_96_wellplate_360uL_Fb(name="tracked_plate")
plt_car[2] = tracked_plate

tracked_plate.get_well("A1").tracker.set_liquids([(Liquid.WATER, 200)])  # or (None, 200)
print(tracked_plate.get_well("A1").tracker.get_used_volume())            # 200
print(tracked_tips.get_item("A1").tracker.has_tip)                       # True

await lh.pick_up_tips(tracked_tips["A1"])
await lh.aspirate(tracked_plate["A1"], vols=[50])
await lh.dispense(tracked_plate["A2"], vols=[50])
await lh.return_tips()
print(tracked_plate.get_well("A1").tracker.get_used_volume(),
      tracked_plate.get_well("A2").tracker.get_used_volume())            # 150 50
```

Tracker methods: `set_liquids`, `set_volume`, `get_used_volume`, `get_free_volume`, `get_liquids` for wells; `has_tip` for tip spots. Tracking can be switched off per resource with `tracker.disable()`.

## Saving layouts and state

```python
lh.deck.save("deck_layout.json")                    # layout: resource definitions and positions
lh.deck.save_state_to_file("deck_state.json")       # state: tips present, liquid volumes

from pylabrobot.resources import Deck

deck = Deck.load_from_json_file("deck_layout.json")
deck.load_state_from_file("deck_state.json")
```

`serialize()` / `Resource.deserialize(...)` and `serialize_all_state()` / `load_all_state(...)` give the same data as dictionaries. Commit the layout JSON with the protocol so every run uses the same deck.

## Defining custom labware

Build a plate from its measured geometry with `create_ordered_items_2d`:

```python
from pylabrobot.resources import (
    CrossSectionType,
    Plate,
    Well,
    WellBottomType,
    create_ordered_items_2d,
)


def my_24_wellplate_3400uL_Fb(name: str) -> Plate:
    """24-well plate; all dimensions in mm from the vendor drawing (check before use)."""
    return Plate(
        name=name,
        size_x=127.76, size_y=85.48, size_z=20.0,
        model="my_24_wellplate_3400uL_Fb",
        ordered_items=create_ordered_items_2d(
            Well,
            num_items_x=6, num_items_y=4,
            dx=9.0, dy=6.0, dz=1.0,          # offset of well A1's corner from the plate origin
            item_dx=19.3, item_dy=19.3,      # well pitch
            size_x=16.3, size_y=16.3, size_z=18.0,
            bottom_type=WellBottomType.FLAT,
            cross_section_type=CrossSectionType.CIRCLE,
            max_volume=3400,
        ),
    )


custom = my_24_wellplate_3400uL_Fb(name="custom_plate")
print(custom.num_items_x, custom.num_items_y, custom.get_well("D6").max_volume)
```

Verify a new definition on the robot with a slow, liquid-free run (or the visualizer) before trusting it, and consider contributing tested definitions upstream.
