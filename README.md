# TeslaBox – Center Console Insert (Model Y Juniper *Standard*)

*[Deutsch](README.de.md)*

A 3D-printable organizer insert for the deep armrest bin of the Tesla
Model Y "Juniper" Standard center console (2025/2026). Parametric CAD
model (Python/CadQuery, real fillets, OCCT kernel) instead of a fixed
STL – all dimensions can be adjusted to the actual vehicle.

![TeslaBox](teslabox_iso.png)

Printed and installed:

![Installed in the vehicle](teslabox_eingebaut.jpg)
![Removed, with contents](teslabox_ausgebaut.jpg)

## What this is

The bin has a small **ledge** running around the top, a few mm below
the console surface, present only on the two long sides. The insert
has a matching narrow **collar** on both long sides that rests exactly
in that ledge: the part *hangs in place* and stays flush with the
console surface instead of dropping to the bottom of the bin. The real
bin narrows slightly toward the bottom, so the body is conically
tapered below the collar, making it grip lightly as it's inserted
instead of rattling around.

The front has a solid block with two upright slots side by side for
credit cards (card held vertically, 85.6 × 54 mm). An open **coin
channel** runs along the top of one side wall, with the underside
shaped as a wedge so it prints fully support-free on an FDM printer.
The rest is open storage space.

All construction details (dimensions, reasoning, discarded
alternatives) are documented in detail in [`SPEC.md`](SPEC.md) – a
tool-independent description, not tied to CadQuery.

## ⚠️ Measure first

The interior dimensions of the bin aren't documented anywhere (Tesla
doesn't publish them, accessory vendors only list exterior dimensions,
and the *Standard* console differs from Premium/Performance). Before
printing, check the parameters in `teslabox.py` (ledge dimensions, bin
depth, corner radius) against the actual vehicle.

## Files

| File | Purpose |
|------|---------|
| `teslabox.py` | main model (CadQuery / OCCT) |
| `teslabox.stl` | ready-to-print export |
| `teslabox_iso.png` | preview image (above) |
| `SPEC.md` | detailed, tool-independent object description |
| `render.py` | generate preview PNGs from an STL (`render.py <stl> <png> [az] [el]`) |

## Toolchain (one-time setup)

```bash
curl -sSL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
python3 -m venv /tmp/cadenv
/tmp/cadenv/bin/python /tmp/get-pip.py
/tmp/cadenv/bin/pip install --only-binary :all: cadquery
```

```bash
/tmp/cadenv/bin/python teslabox.py
```

## Key parameters in `teslabox.py`

| Parameter | Purpose |
|-----------|---------|
| `FALZ_BREITE`, `FALZ_TIEFE` | measured ledge opening width / ledge step depth |
| `FACH_BREITE`, `FACH_TIEFE` | measured interior dimensions of the bin |
| `ECK_RADIUS` | measured interior corner radius |
| `GESAMT_LAENGE` | build length of the insert in X (the bin is longer – the insert only covers the front part) |
| `VORNE_FREI` | clearance at the front with no collar (room for the card slots) |
| `KORPUS_HOEHE` | overall height of the insert |
| `WAND`, `BODEN` | wall / floor thickness |
| `N_SLOT`, `SLOT_X_DICKE`, `SLOT_Y_LAENGE`, `SLOT_TIEFE` | number/dimensions of the card slots |
| `MUENZE_R`, `MUENZE_GERADE` | cross-section of the coin channel |
| `BODEN_VERJUENGUNG` | taper per side at the bottom, so the insert grips |

## Printing

PETG (heat-resistant for a parked car in summer), 0.2 mm layer height,
3 walls, 12% infill, no supports. Optionally, thin felt/TPE strips
under the collar to reduce rattling.
