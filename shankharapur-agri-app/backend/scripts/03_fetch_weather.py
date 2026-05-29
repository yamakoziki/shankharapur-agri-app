"""
Fetch historical and forecast weather data from Open-Meteo for 3 elevation zones.
Applies lapse-rate correction (−0.65°C/100m) relative to zone target elevations.

Output:
  backend/data/processed/weather_zones.json   (monthly climate stats per zone)
  backend/data/processed/forecast.json        (14-day forecast per zone)
"""
import requests
import json
import time
from pathlib import Path
from datetime import date, timedelta

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ZONES = {
    "lowland": {
        "lat": 27.730, "lon": 85.464,
        "name": "Sankhu Area",
        "elevation_target": 1425,
    },
    "mid": {
        "lat": 27.748, "lon": 85.484,
        "name": "Lapsiphedi Area",
        "elevation_target": 1600,
    },
    "highland": {
        "lat": 27.762, "lon": 85.506,
        "name": "Sangachok Area",
        "elevation_target": 1800,
    },
}

DAILY_VARS = "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration"
LAPSE_RATE = 0.0065  # °C per metre


def apply_lapse_correction(data: dict, api_elevation: float, target_elevation: float) -> dict:
    delta = (api_elevation - target_elevation) * LAPSE_RATE
    daily = data.get("daily", {})
    for key in ("temperature_2m_max", "temperature_2m_min", "temperature_2m_mean"):
        if key in daily:
            daily[key] = [
                round(v - delta, 2) if v is not None else None
                for v in daily[key]
            ]
    return data


def fetch_historical(zone_key: str, start: str, end: str) -> dict:
    z = ZONES[zone_key]
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={z['lat']}&longitude={z['lon']}"
        f"&start_date={start}&end_date={end}"
        f"&daily={DAILY_VARS}"
        f"&timezone=Asia%2FKathmandu"
    )
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()
    api_elev = data.get("elevation", z["elevation_target"])
    return apply_lapse_correction(data, api_elev, z["elevation_target"])


def fetch_forecast(zone_key: str) -> dict:
    z = ZONES[zone_key]
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={z['lat']}&longitude={z['lon']}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
        f"&forecast_days=14"
        f"&timezone=Asia%2FKathmandu"
    )
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    api_elev = data.get("elevation", z["elevation_target"])
    return apply_lapse_correction(data, api_elev, z["elevation_target"])


def compute_monthly_climate(historical_data: dict) -> dict:
    """
    Aggregate daily historical data into monthly stats over the full record.
    Returns {month(1-12): {temp_mean, temp_max, temp_min, precip_sum, et0_sum, count}}
    """
    daily = historical_data.get("daily", {})
    dates = daily.get("time", [])
    temps_mean = daily.get("temperature_2m_mean", [None] * len(dates))
    temps_max = daily.get("temperature_2m_max", [None] * len(dates))
    temps_min = daily.get("temperature_2m_min", [None] * len(dates))
    precip = daily.get("precipitation_sum", [None] * len(dates))
    et0 = daily.get("et0_fao_evapotranspiration", [None] * len(dates))

    monthly: dict = {m: {"temps_mean": [], "temps_max": [], "temps_min": [], "precip": [], "et0": []} for m in range(1, 13)}
    for i, d in enumerate(dates):
        month = int(d[5:7])
        if temps_mean[i] is not None:
            monthly[month]["temps_mean"].append(temps_mean[i])
        if temps_max[i] is not None:
            monthly[month]["temps_max"].append(temps_max[i])
        if temps_min[i] is not None:
            monthly[month]["temps_min"].append(temps_min[i])
        if precip[i] is not None:
            monthly[month]["precip"].append(precip[i])
        if et0[i] is not None:
            monthly[month]["et0"].append(et0[i])

    result = {}
    for m, vals in monthly.items():
        def avg(lst): return round(sum(lst) / len(lst), 1) if lst else None
        def total(lst): return round(sum(lst), 1) if lst else None
        # precip_mean = avg daily × days in month approach
        days_in_month = len(vals["precip"]) // max(1, len(set(str(m))))
        n_years = max(1, len(vals["precip"]) // 30) if vals["precip"] else 1
        result[m] = {
            "temp_mean": avg(vals["temps_mean"]),
            "temp_max": avg(vals["temps_max"]),
            "temp_min": avg(vals["temps_min"]),
            "precip_monthly_avg": round(sum(vals["precip"]) / n_years, 1) if vals["precip"] else None,
            "et0_monthly_avg": round(sum(vals["et0"]) / n_years, 1) if vals["et0"] else None,
            "n_days": len(vals["temps_mean"]),
        }
    return result


def main():
    # Fetch last 5 years of history for climate stats
    end_date = (date.today() - timedelta(days=1)).isoformat()
    start_date = date(date.today().year - 5, 1, 1).isoformat()

    weather_zones = {}
    forecast_out = {}

    for zone_key, zone_info in ZONES.items():
        print(f"\n=== Zone: {zone_key} ({zone_info['name']}) ===")

        print(f"  Fetching historical {start_date} → {end_date}...")
        try:
            hist = fetch_historical(zone_key, start_date, end_date)
            climate = compute_monthly_climate(hist)
            weather_zones[zone_key] = {
                "name": zone_info["name"],
                "elevation": zone_info["elevation_target"],
                "monthly_climate": climate,
            }
            print(f"  OK — {len(hist['daily'].get('time', []))} days")
        except Exception as e:
            print(f"  ERROR: {e}")
            weather_zones[zone_key] = {"name": zone_info["name"], "elevation": zone_info["elevation_target"], "monthly_climate": {}}

        time.sleep(1)

        print(f"  Fetching 14-day forecast...")
        try:
            fc = fetch_forecast(zone_key)
            forecast_out[zone_key] = {
                "name": zone_info["name"],
                "daily": fc.get("daily", {}),
            }
            print(f"  OK")
        except Exception as e:
            print(f"  ERROR: {e}")
            forecast_out[zone_key] = {"name": zone_info["name"], "daily": {}}

        time.sleep(1)

    zones_path = PROCESSED_DIR / "weather_zones.json"
    with open(zones_path, "w") as f:
        json.dump(weather_zones, f, separators=(",", ":"))
    print(f"\nSaved: {zones_path}")

    forecast_path = PROCESSED_DIR / "forecast.json"
    with open(forecast_path, "w") as f:
        json.dump(forecast_out, f, separators=(",", ":"))
    print(f"Saved: {forecast_path}")


if __name__ == "__main__":
    main()
