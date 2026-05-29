"""Open-Meteo weather/AQI helpers — Layer 5 demos pull live AQI here.

Kept tiny: the dashboard's Layer 5 demo card calls
`fetch_air_quality(lat, lon)` so the AQI gate runs against real data
instead of a hardcoded value. No API key required.
"""

from __future__ import annotations

from typing import Optional

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_AQI = "https://air-quality-api.open-meteo.com/v1/air-quality"
_WEATHER = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT = 8


def geocode(city: str) -> Optional[dict]:
    if requests is None or not city:
        return None
    try:
        r = requests.get(_GEOCODE, params={"name": city, "count": 1},
                         timeout=_TIMEOUT)
        if not r.ok:
            return None
        data = r.json().get("results") or []
        if not data:
            return None
        m = data[0]
        return {"lat": m["latitude"], "lon": m["longitude"],
                "name": m.get("name", city), "country": m.get("country", "")}
    except Exception:
        return None


def fetch_weather(lat: float, lon: float) -> Optional[dict]:
    if requests is None:
        return None
    try:
        r = requests.get(_WEATHER, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                       "wind_speed_10m,precipitation",
        }, timeout=_TIMEOUT)
        if not r.ok:
            return None
        cur = (r.json() or {}).get("current") or {}
        return {
            "temp_c": cur.get("temperature_2m"),
            "feels_like_c": cur.get("apparent_temperature"),
            "humidity_pct": cur.get("relative_humidity_2m"),
            "wind_kmh": cur.get("wind_speed_10m"),
            "precip_mm": cur.get("precipitation"),
        }
    except Exception:
        return None


def fetch_air_quality(lat: float, lon: float) -> Optional[dict]:
    if requests is None:
        return None
    try:
        r = requests.get(_AQI, params={
            "latitude": lat, "longitude": lon,
            "current": "european_aqi,pm2_5,pm10,nitrogen_dioxide,ozone,carbon_monoxide",
        }, timeout=_TIMEOUT)
        if not r.ok:
            return None
        cur = (r.json() or {}).get("current") or {}
        return {
            "european_aqi": cur.get("european_aqi"),
            "pm2_5": cur.get("pm2_5"),
            "pm10": cur.get("pm10"),
            "no2": cur.get("nitrogen_dioxide"),
            "o3": cur.get("ozone"),
            "co": cur.get("carbon_monoxide"),
        }
    except Exception:
        return None


def aqi_level(european_aqi: Optional[float]) -> str:
    if european_aqi is None:
        return "unknown"
    a = european_aqi
    if a <= 20: return "good"
    if a <= 40: return "fair"
    if a <= 60: return "moderate"
    if a <= 80: return "poor"
    if a <= 100: return "very_poor"
    return "extremely_poor"
