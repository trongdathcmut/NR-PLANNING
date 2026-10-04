"""User-editable configuration for the 5G NR planning simulation."""

# --- Radio / NR assumptions ---
FC_GHZ = 3.5
BANDWIDTH_MHZ = 100.0
SCS_KHZ = 30.0
N_RB = 273                  # 100 MHz @ 30 kHz SCS (FR1)
EIRP_DBM = 64.0             # educational planning assumption, total-cell equivalent EIRP
UE_GAIN_DBI = 0.0
SYSTEM_LOSS_DB = 2.0
NOISE_FIGURE_DB = 7.0
H_BS_M = 25.0
H_UT_M = 1.5

# Massive-MIMO abstraction: desired-link beam gain and interference suppression.
MIMO_SERVING_GAIN_DB = 6.0
INTERFERENCE_REJECTION_DB = 3.0

# --- Spatial simulation ---
GRID_STEP_M = 70.0
RANDOM_SEED = 2026
USE_AIRPORT_OPEN_AREA_HEURISTIC = True
AIRPORT_DEMAND_WEIGHT = 0.35
URBAN_DEMAND_WEIGHT = 1.0

# If KML contains polygons named BLOCKAGE*, NLOS*, OBSTACLE*, each crossed link
# receives this additional loss. Draw such polygons in Google Earth to make the
# simulation site-specific without touching Python code.
BLOCKAGE_EXTRA_LOSS_DB = 20.0

# --- KPI thresholds ---
RSRP_EXCELLENT_DBM = -85.0
RSRP_GOOD_DBM = -95.0
RSRP_FAIR_DBM = -105.0
SINR_GOOD_DB = 13.0
SINR_USABLE_DB = 0.0
WEAK_RSRP_DBM = -105.0
WEAK_SINR_DB = 0.0

# Throughput mapping (Shannon-like, intentionally simple for a planning assignment)
SPECTRAL_EFFICIENCY_CAP = 7.4
IMPLEMENTATION_EFFICIENCY = 0.72

# Planning recommendation
MIN_WEAK_CLUSTER_POINTS = 5
