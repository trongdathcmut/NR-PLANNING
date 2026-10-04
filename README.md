# 5G NR Python Planning – Tân Sơn Nhất

Mini planning/digital-twin project built from the Google Earth KML exported for the assignment.

## What it does

1. Reads the **study polygon** and every `gNB-*` point directly from KML.
2. Converts WGS84 coordinates to a local metric CRS (UTM).
3. Creates a UE/grid inside the study area.
4. Runs a reproducible **3GPP TR 38.901 Urban Macro (UMa)** LOS/NLOS path-loss simulation.
5. Adds log-normal shadow fading.
6. Uses a transparent Massive-MIMO abstraction: serving-link beam gain + interference suppression.
7. Calculates an RSRP-like map, serving cell, SINR, overlap count, and estimated throughput.
8. Detects weak zones and proposes one **candidate** new site for further inspection in Google Earth.
9. Exports PNG figures, CSV tables, and an interactive HTML map.

## Very useful trick: draw blockages in Google Earth

If you draw extra polygons in Google Earth and name them like:

- `BLOCKAGE-01`
- `OBSTACLE-A`
- `NLOS-BUILDINGS`
- `CHE KHUAT 1`

then export the KML again. The Python model automatically treats links crossing those polygons as blocked and adds `BLOCKAGE_EXTRA_LOSS_DB` from `config.py`.

This lets the report show a clear loop:

**Google Earth survey → Python RF simulation → weak-zone detection → move/add gNB → export KML again → rerun.**

## Run on Windows

Open terminal in this folder:

```bash
python -m pip install -r requirements.txt
python main.py
```

To run another KML:

```bash
python main.py "data/your_new_map.kml"
```

## Outputs

`results/`

- `01_layout.png`
- `02_rsrp.png`
- `03_sinr.png`
- `04_serving_cell.png`
- `05_throughput.png`
- `06_overlap.png`
- `07_rsrp_cdf.png`
- `08_sinr_cdf.png`
- `site_kpis.csv`
- `network_kpis.csv`
- `grid_results.csv`
- `interactive_map.html`

## Assumptions to state in the report

- Carrier: **3.5 GHz**.
- Scenario: **Urban Macro (UMa)**.
- Bandwidth: **100 MHz**, 30 kHz SCS, 273 RB.
- gNB antenna height: **25 m**; UE height: **1.5 m**.
- KML altitude is terrain/reference altitude; the simulation uses the configured antenna height.
- RSRP is an **RSRP-like planning estimate** derived from equivalent EIRP, path loss and per-RE power allocation. It should be calibrated if real vendor/field parameters are available.
- The optional central airport/open-area mask is only a heuristic; it is not a replacement for real 3D building/clutter data.
- Throughput is Shannon-like with an implementation efficiency and spectral-efficiency cap; it is for comparative planning, not a vendor scheduler prediction.

## References used for the model

- 3GPP TR 38.901: channel model for 0.5–100 GHz; UMa LOS/NLOS path-loss equations.
- The supplied ZTE 5G Planning material: plan sites based on coverage/capacity, simulate, find over/weak coverage, then remove redundant sites or add weak-coverage sites.

## Suggested report story

1. Google Earth defines the real study area and initial gNB locations.
2. Python imports those locations automatically.
3. 3GPP UMa predicts propagation at 3.5 GHz.
4. Each grid point attaches to the strongest cell.
5. SINR includes co-channel interference from the other gNBs.
6. Massive MIMO is represented by a serving-beam gain and interference-rejection term.
7. Weak/overlap zones are identified.
8. The candidate site is checked again in Google Earth for actual deployability (empty land, rooftop, power/backhaul/access).
9. Iterate until KPI targets are acceptable.
