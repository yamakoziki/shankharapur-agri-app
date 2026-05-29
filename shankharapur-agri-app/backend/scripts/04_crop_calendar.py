"""
Compute crop × zone × sowing-month suitability scores and emit JSON for the frontend.

score = temp_suitability(40%) + rain_suitability(20%) + harvest_price(40%)

Output: backend/data/processed/crop_scores.json
"""
import json
import argparse
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

CROP_REQUIREMENTS = {
    "Tomato": {
        "name_np": "गोलभेडा",
        "temp_min": 10, "temp_opt": 22, "temp_max": 32,
        "rain_mm_season": 400,
        "growing_days": 90,
        "elevation_max": 2000,
        "sowing_months": [1, 2, 3, 8, 9],
    },
    "Tomato Small": {
        "name_np": "गोलभेडा (सानो)",
        "temp_min": 10, "temp_opt": 22, "temp_max": 32,
        "rain_mm_season": 380,
        "growing_days": 85,
        "elevation_max": 2000,
        "sowing_months": [1, 2, 3, 8, 9],
    },
    "Potato": {
        "name_np": "आलु",
        "temp_min": 7, "temp_opt": 18, "temp_max": 25,
        "rain_mm_season": 300,
        "growing_days": 80,
        "elevation_max": 3000,
        "sowing_months": [1, 2, 9, 10],
    },
    "Potato Red": {
        "name_np": "रातो आलु",
        "temp_min": 7, "temp_opt": 17, "temp_max": 25,
        "rain_mm_season": 300,
        "growing_days": 80,
        "elevation_max": 3000,
        "sowing_months": [1, 2, 9, 10],
    },
    "Cauliflower": {
        "name_np": "काउली",
        "temp_min": 5, "temp_opt": 17, "temp_max": 25,
        "rain_mm_season": 350,
        "growing_days": 70,
        "elevation_max": 2500,
        "sowing_months": [8, 9, 10],
    },
    "Cabbage": {
        "name_np": "बन्दा",
        "temp_min": 5, "temp_opt": 15, "temp_max": 22,
        "rain_mm_season": 300,
        "growing_days": 80,
        "elevation_max": 2500,
        "sowing_months": [8, 9, 10],
    },
    "Onion": {
        "name_np": "प्याज",
        "temp_min": 10, "temp_opt": 20, "temp_max": 28,
        "rain_mm_season": 250,
        "growing_days": 120,
        "elevation_max": 1800,
        "sowing_months": [10, 11, 12],
    },
    "Onion Green": {
        "name_np": "हरियो प्याज",
        "temp_min": 10, "temp_opt": 18, "temp_max": 26,
        "rain_mm_season": 200,
        "growing_days": 60,
        "elevation_max": 2000,
        "sowing_months": [9, 10, 11, 2, 3],
    },
    "Radish": {
        "name_np": "मूला",
        "temp_min": 5, "temp_opt": 15, "temp_max": 22,
        "rain_mm_season": 200,
        "growing_days": 40,
        "elevation_max": 2500,
        "sowing_months": [8, 9, 10, 11],
    },
    "Spinach": {
        "name_np": "पालुंगो",
        "temp_min": 5, "temp_opt": 16, "temp_max": 24,
        "rain_mm_season": 200,
        "growing_days": 45,
        "elevation_max": 2500,
        "sowing_months": [9, 10, 11, 2, 3],
    },
    "Carrot": {
        "name_np": "गाजर",
        "temp_min": 7, "temp_opt": 16, "temp_max": 24,
        "rain_mm_season": 250,
        "growing_days": 70,
        "elevation_max": 2500,
        "sowing_months": [8, 9, 10],
    },
    "Pumpkin": {
        "name_np": "फर्सी",
        "temp_min": 18, "temp_opt": 26, "temp_max": 35,
        "rain_mm_season": 400,
        "growing_days": 90,
        "elevation_max": 1900,
        "sowing_months": [3, 4, 5],
    },
    "Bitter Gourd": {
        "name_np": "करेला",
        "temp_min": 20, "temp_opt": 28, "temp_max": 38,
        "rain_mm_season": 450,
        "growing_days": 70,
        "elevation_max": 1800,
        "sowing_months": [3, 4, 5],
    },
    "Snake Gourd": {
        "name_np": "चिचिण्डो",
        "temp_min": 20, "temp_opt": 28, "temp_max": 38,
        "rain_mm_season": 450,
        "growing_days": 70,
        "elevation_max": 1800,
        "sowing_months": [3, 4, 5],
    },
    "Beans": {
        "name_np": "सिमी",
        "temp_min": 10, "temp_opt": 22, "temp_max": 30,
        "rain_mm_season": 350,
        "growing_days": 55,
        "elevation_max": 2200,
        "sowing_months": [3, 4, 8, 9],
    },
    "Cucumber": {
        "name_np": "काक्रो",
        "temp_min": 18, "temp_opt": 28, "temp_max": 38,
        "rain_mm_season": 400,
        "growing_days": 60,
        "elevation_max": 1800,
        "sowing_months": [3, 4, 5],
    },
    "Green Peas": {
        "name_np": "केराउ",
        "temp_min": 5, "temp_opt": 14, "temp_max": 22,
        "rain_mm_season": 200,
        "growing_days": 70,
        "elevation_max": 2500,
        "sowing_months": [9, 10, 11],
    },
    "Maize Green": {
        "name_np": "हरियो मकै",
        "temp_min": 16, "temp_opt": 24, "temp_max": 34,
        "rain_mm_season": 500,
        "growing_days": 80,
        "elevation_max": 2200,
        "sowing_months": [3, 4, 5],
    },
    "Ginger": {
        "name_np": "अदुवा",
        "temp_min": 20, "temp_opt": 26, "temp_max": 32,
        "rain_mm_season": 600,
        "growing_days": 180,
        "elevation_max": 1800,
        "sowing_months": [4, 5],
    },
    "Garlic": {
        "name_np": "लसुन",
        "temp_min": 5, "temp_opt": 15, "temp_max": 24,
        "rain_mm_season": 200,
        "growing_days": 150,
        "elevation_max": 2500,
        "sowing_months": [10, 11],
    },
}

ZONE_ELEVATIONS = {
    "lowland": 1425,
    "mid": 1600,
    "highland": 1800,
}


def load_weather() -> dict:
    path = PROCESSED_DIR / "weather_zones.json"
    if not path.exists():
        raise FileNotFoundError(f"Run 03_fetch_weather.py first: {path}")
    with open(path) as f:
        return json.load(f)


def load_prices() -> dict:
    path = PROCESSED_DIR / "prices_monthly.json"
    if not path.exists():
        raise FileNotFoundError(f"Run 02_process_prices.py first: {path}")
    with open(path) as f:
        return json.load(f)


def calc_sowing_score(
    crop_key: str,
    zone_key: str,
    sow_month: int,
    weather_zones: dict,
    price_monthly_avg: dict,
) -> dict:
    req = CROP_REQUIREMENTS[crop_key]
    zone_elev = ZONE_ELEVATIONS.get(zone_key, 1500)

    # Outside the agronomic sowing window → blank cell in frontend
    if sow_month not in req["sowing_months"]:
        return {"score": None}

    if zone_elev > req["elevation_max"]:
        return {"score": 0, "temp_score": 0, "rain_score": 0, "price_score": 0, "harvest_month": 0, "unsuitable_elevation": True}

    growing_months = max(1, req["growing_days"] // 30)
    harvest_month = (sow_month - 1 + growing_months) % 12 + 1

    climate = weather_zones.get(zone_key, {}).get("monthly_climate", {})

    # Temperature score averaged over growing period
    temp_scores = []
    for i in range(growing_months):
        mo = str((sow_month - 1 + i) % 12 + 1)
        t = (climate.get(int(mo), {}) or {}).get("temp_mean")
        if t is None:
            temp_scores.append(50)
            continue
        if t < req["temp_min"] or t > req["temp_max"]:
            temp_scores.append(0)
        else:
            deviation = abs(t - req["temp_opt"])
            range_half = max(req["temp_max"] - req["temp_opt"], req["temp_opt"] - req["temp_min"])
            temp_scores.append(max(0, 100 - (deviation / range_half) * 100))
    temp_score = sum(temp_scores) / len(temp_scores) if temp_scores else 50

    # Rainfall score over growing period
    total_rain = 0
    for i in range(growing_months):
        mo = int((sow_month - 1 + i) % 12 + 1)
        precip = (climate.get(mo, {}) or {}).get("precip_monthly_avg") or 0
        total_rain += precip
    rain_score = min(100, total_rain / req["rain_mm_season"] * 100)
    if total_rain > req["rain_mm_season"] * 1.5:
        rain_score *= 0.8

    # Harvest-month price score
    crop_monthly = price_monthly_avg.get(crop_key, {})
    price_score = float(crop_monthly.get(str(harvest_month), 50) or 50)

    # Weights: market price 60%, temperature fit 25%, rainfall 15%
    score = temp_score * 0.25 + rain_score * 0.15 + price_score * 0.60

    return {
        "score": round(score, 1),
        "temp_score": round(temp_score, 1),
        "rain_score": round(rain_score, 1),
        "price_score": round(price_score, 1),
        "harvest_month": harvest_month,
    }


def main(output_dir: Path | None = None):
    out_dir = output_dir or PROCESSED_DIR

    print("Loading weather data...")
    weather_zones = load_weather()

    print("Loading price data...")
    prices = load_prices()
    price_monthly_avg = prices.get("monthly_avg", {})

    print("Computing crop scores...")
    crop_scores: dict = {}

    for zone_key in ZONE_ELEVATIONS:
        crop_scores[zone_key] = {}
        for crop_key in CROP_REQUIREMENTS:
            crop_scores[zone_key][crop_key] = {}
            for sow_month in range(1, 13):
                result = calc_sowing_score(crop_key, zone_key, sow_month, weather_zones, price_monthly_avg)
                crop_scores[zone_key][crop_key][sow_month] = result

    import math

    def sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    out_path = out_dir / "crop_scores.json"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(sanitize(crop_scores), f, separators=(",", ":"))
    print(f"Saved: {out_path}")

    # Also write crop metadata (name_np, growing_days, etc.)
    meta = {
        k: {
            "name_np": v["name_np"],
            "growing_days": v["growing_days"],
            "elevation_max": v["elevation_max"],
            "sowing_months": v["sowing_months"],
            "temp_opt": v["temp_opt"],
        }
        for k, v in CROP_REQUIREMENTS.items()
    }
    meta_path = out_dir / "crop_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, separators=(",", ":"), ensure_ascii=False)
    print(f"Saved: {meta_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    main(args.output)
