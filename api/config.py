"""
Configuration module for AI FireGuard.
Contains NASA FIRMS API settings, bounding box coordinates, ML thresholds,
and designated safe evacuation centers in Uttarakhand.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# NASA FIRMS API Settings
# VIIRS S-NPP Near Real-Time Active Fire API
NASA_FIRMS_MAP_KEY = os.getenv("NASA_FIRMS_MAP_KEY", "43f0a33302cc584d7d63c4aeeb41dd48")
NASA_FIRMS_SOURCE = "VIIRS_SNPP_SP"

# Carto Basemap API Key
CARTO_BASEMAP_KEY = os.getenv("CARTO_BASEMAP_KEY", "cb1_411n_1_52d3478f6a48862b43f7f2bd")

# Uttarakhand Region Bounding Box [min_lon, min_lat, max_lon, max_lat]
UTTARAKHAND_BBOX = [77.5, 28.7, 81.1, 31.5]
UTTARAKHAND_BBOX_STR = f"{UTTARAKHAND_BBOX[0]},{UTTARAKHAND_BBOX[1]},{UTTARAKHAND_BBOX[2]},{UTTARAKHAND_BBOX[3]}"

# Risk Classification Thresholds (Continuous probability 0.0 - 1.0)
RISK_THRESHOLD_LOW = 0.35
RISK_THRESHOLD_HIGH = 0.70

# Designated Safe Evacuation Destinations in Uttarakhand
SAFE_DESTINATIONS = [
    {
        "id": "shelter_ddn",
        "name": "Dehradun Central Relief & Evacuation Hub",
        "lat": 30.3165,
        "lon": 78.0322,
        "capacity": 2500,
        "type": "District Emergency Center"
    },
    {
        "id": "shelter_rsh",
        "name": "Rishikesh Ganga Riverfront Safe Zone",
        "lat": 30.1033,
        "lon": 78.2948,
        "capacity": 1800,
        "type": "Waterfront Safety Depot"
    },
    {
        "id": "shelter_hdw",
        "name": "Haridwar Bypass Safety Depot",
        "lat": 29.9457,
        "lon": 78.1642,
        "capacity": 3000,
        "type": "Disaster Relief Camp"
    },
    {
        "id": "shelter_ntl",
        "name": "Nainital Lake Safety Compound",
        "lat": 29.3919,
        "lon": 79.4542,
        "capacity": 1200,
        "type": "Hill Station Safe Camp"
    },
    {
        "id": "shelter_hld",
        "name": "Haldwani Regional Sports Complex",
        "lat": 29.2183,
        "lon": 79.5130,
        "capacity": 3500,
        "type": "High Capacity Stadium Hub"
    },
    {
        "id": "shelter_alm",
        "name": "Almora District Stadium Relief Camp",
        "lat": 29.5971,
        "lon": 79.6591,
        "capacity": 1000,
        "type": "Emergency Sheltering Field"
    }
]
