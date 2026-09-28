"""
NASA FIRMS (Fire Information for Resource Management System) Service.
Queries VIIRS S-NPP Active Fire Satellite data for the Uttarakhand region.
Features offline caching fallback for resilient viva and offline demonstrations.
"""

import json
import csv
import io
import math
from typing import List, Dict, Any, Optional
import requests

from api.config import (
    NASA_FIRMS_MAP_KEY,
    NASA_FIRMS_SOURCE,
    UTTARAKHAND_BBOX_STR,
    DATA_DIR
)

CACHE_FILE = DATA_DIR / "uttarakhand_hotspots.json"

class NASAFirmsService:
    def __init__(self, map_key: str = NASA_FIRMS_MAP_KEY):
        self.map_key = map_key
        self.source = NASA_FIRMS_SOURCE
        self.bbox = UTTARAKHAND_BBOX_STR

    def fetch_hotspots(self, date_str: Optional[str] = None, day_range: int = 5) -> Dict[str, Any]:
        """
        Fetch active fire hotspots from NASA FIRMS VIIRS API.
        Falls back to local cached dataset if NASA FIRMS is offline or unreachable.
        """
        # If no date specified, default to peak fire season sample date or latest
        target_date = date_str if date_str else "2026-04-20"
        api_url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
            f"{self.map_key}/{self.source}/{self.bbox}/{day_range}/{target_date}"
        )

        try:
            response = requests.get(api_url, timeout=8, headers={"User-Agent": "AIFireGuard/1.0"})
            if response.status_code == 200 and "latitude,longitude" in response.text:
                hotspots = self._parse_csv(response.text)
                return {
                    "status": "success",
                    "source": "NASA FIRMS (VIIRS Near Real-Time)",
                    "live": True,
                    "date": target_date,
                    "count": len(hotspots),
                    "hotspots": hotspots
                }
            else:
                return self._load_fallback_cache(reason=f"NASA API returned status {response.status_code}")
        except Exception as e:
            return self._load_fallback_cache(reason=f"Network error: {str(e)}")

    def _parse_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        reader = csv.DictReader(io.StringIO(csv_text))
        hotspots = []
        for row in reader:
            try:
                lat = float(row.get("latitude", 0))
                lon = float(row.get("longitude", 0))
                frp = float(row.get("frp", 0) or 0)
                brightness = float(row.get("bright_ti4", 0) or 0)
                confidence = row.get("confidence", "nominal")
                
                # Confidence translation ('l': low, 'n': nominal, 'h': high)
                conf_label = "High" if confidence == "h" else ("Medium" if confidence == "n" else "Low")

                hotspots.append({
                    "lat": lat,
                    "lon": lon,
                    "frp": frp,
                    "brightness": brightness,
                    "confidence": conf_label,
                    "satellite": row.get("satellite", "VIIRS"),
                    "date": row.get("acq_date", ""),
                    "time": row.get("acq_time", ""),
                    "daynight": "Day" if row.get("daynight") == "D" else "Night"
                })
            except (ValueError, TypeError):
                continue

        # Sort by Fire Radiative Power (intensity)
        hotspots.sort(key=lambda x: x["frp"], reverse=True)
        return hotspots

    def _load_fallback_cache(self, reason: str = "") -> Dict[str, Any]:
        """Loads cached NASA FIRMS hotspots recorded for Uttarakhand."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                
                formatted = []
                for item in raw_data:
                    lat = float(item.get("latitude", 0))
                    lon = float(item.get("longitude", 0))
                    frp = float(item.get("frp", 0) or 0)
                    brightness = float(item.get("bright_ti4", 0) or 0)
                    conf = item.get("confidence", "n")
                    conf_label = "High" if conf == "h" else ("Medium" if conf == "n" else "Low")

                    formatted.append({
                        "lat": lat,
                        "lon": lon,
                        "frp": frp,
                        "brightness": brightness,
                        "confidence": conf_label,
                        "satellite": item.get("satellite", "VIIRS"),
                        "date": item.get("acq_date", "2026-04-20"),
                        "time": item.get("acq_time", "0803"),
                        "daynight": "Day" if item.get("daynight") == "D" else "Night"
                    })
                
                return {
                    "status": "success",
                    "source": "NASA FIRMS (Local Cached Satellite Baseline)",
                    "live": False,
                    "fallback_note": reason,
                    "date": "2026-04-20",
                    "count": len(formatted),
                    "hotspots": formatted
                }
            except Exception as read_err:
                pass

        return {
            "status": "error",
            "source": "None",
            "live": False,
            "count": 0,
            "hotspots": [],
            "error": reason
        }

    @staticmethod
    def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine formula to compute distance between two GPS coordinates in km."""
        r = 6371.0 # Earth radius in km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0)**2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c

firms_service = NASAFirmsService()
