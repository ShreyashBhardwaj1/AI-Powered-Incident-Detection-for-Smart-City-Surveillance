# backend/location.py  (or wherever your Overpass logic lives)

import requests
import time
import logging

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",  # add this one
    "https://overpass.private.coffee/api/interpreter",    # add this one
]

def query_overpass(amenity: str, lat: float, lon: float, radius: int = 3000) -> list:
    query = f"""
    [out:json][timeout:30];
    node[amenity={amenity}](around:{radius},{lat},{lon});
    out body 5;
    """
    
    for i, mirror in enumerate(OVERPASS_MIRRORS):
        wait = 2 ** i  # exponential backoff: 1s, 2s, 4s, 8s
        try:
            logger.info(f"[location] Trying {mirror} for {amenity}...")
            resp = requests.post(
                mirror,
                data={"data": query},
                timeout=20,  # increased from default
                headers={"User-Agent": "SmartCityApp/1.0"}
            )
            resp.raise_for_status()
            elements = resp.json().get("elements", [])
            if elements:
                logger.info(f"[location] ✅ Got {len(elements)} results from {mirror}")
                return elements
            logger.warning(f"[location] {mirror} returned 0 results for {amenity}")
        except requests.exceptions.Timeout:
            logger.warning(f"[location] {mirror} timed out for {amenity}, waiting {wait}s...")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"[location] {mirror} HTTP error for {amenity}: {e}")
        except Exception as e:
            logger.warning(f"[location] {mirror} failed for {amenity}: {e}")
        
        if i < len(OVERPASS_MIRRORS) - 1:
            time.sleep(wait)
    
    # Final fallback: Nominatim (OSM search API)
    logger.warning(f"[location] All Overpass mirrors failed — trying Nominatim fallback for {amenity}")
    return nominatim_fallback(amenity, lat, lon)


def nominatim_fallback(amenity: str, lat: float, lon: float) -> list:
    """Use Nominatim as a last resort when Overpass is down."""
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": amenity,
                "format": "json",
                "limit": 5,
                "viewbox": f"{lon-0.05},{lat+0.05},{lon+0.05},{lat-0.05}",
                "bounded": 1,
            },
            timeout=15,
            headers={"User-Agent": "SmartCityApp/1.0"}
        )
        resp.raise_for_status()
        results = resp.json()
        logger.info(f"[location] Nominatim returned {len(results)} results for {amenity}")
        # Normalize to Overpass-like format
        return [{"lat": r["lat"], "lon": r["lon"], "tags": {"name": r.get("display_name", "")}} for r in results]
    except Exception as e:
        logger.error(f"[location] Nominatim fallback also failed for {amenity}: {e}")
        return []
    
import requests

def _haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def get_nearby_services(lat: float, lon: float) -> dict:
    OVERPASS_URL = "https://overpass-api.de/api/interpreter"
    results = {"hospitals": [], "police": []}
    for amenity, key in [("hospital", "hospitals"), ("police", "police")]:
        query = f"""
        [out:json][timeout:10];
        (
          node["amenity"="{amenity}"](around:3000,{lat},{lon});
          way["amenity"="{amenity}"](around:3000,{lat},{lon});
        );
        out center 5;
        """
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=12)
            elements = resp.json().get("elements", [])
            places = []
            for el in elements:
                el_lat = el.get("lat") or el.get("center", {}).get("lat")
                el_lon = el.get("lon") or el.get("center", {}).get("lon")
                if el_lat is None: continue
                places.append({
                    "name": el.get("tags", {}).get("name", "Unnamed"),
                    "type": amenity,
                    "lat": el_lat,
                    "lon": el_lon,
                    "distance_km": round(_haversine(lat, lon, el_lat, el_lon), 2)
                })
            places.sort(key=lambda p: p["distance_km"])
            results[key] = places[:5]
        except Exception as e:
            print(f"[location] {amenity} query failed: {e}")
    return results