"""
Monthly price aggregation and sell_score computation.

Input:  backend/data/raw/kalimati_combined.csv
Output: backend/data/processed/kalimati_monthly.csv
        Columns: commodity, month, year, avg_price, min_price, max_price,
                 cv, yoy_change, sell_score
"""
import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Canonical crop names mapped from Kalimati commodity strings
COMMODITY_MAP = {
    # Tomato variants
    "tomato big(nepali)":           "Tomato",
    "tomato big (nepali)":          "Tomato",
    "tomato big(indian)":           "Tomato",
    # Tomato Small
    "tomato small(local)":          "Tomato Small",
    "tomato small (local)":         "Tomato Small",
    "tomato small(tunnel)":         "Tomato Small",
    "tomato small(terai)":          "Tomato Small",
    "tomato small(indian)":         "Tomato Small",
    # Potato
    "potato white":                 "Potato",
    "potato white(indian)":         "Potato",
    "potato white (indian)":        "Potato",
    # Potato Red
    "potato red":                   "Potato Red",
    "potato red(indian)":           "Potato Red",
    "potato red (indian)":          "Potato Red",
    "potato red(mude)":             "Potato Red",
    "potato red(round)":            "Potato Red",
    "potato red(long)":             "Potato Red",
    # Cauliflower
    "cauliflower(local)":           "Cauliflower",
    "cauliflower (local)":          "Cauliflower",
    "cauli local":                  "Cauliflower",
    "cauli local(jyapu)":           "Cauliflower",
    # Cabbage
    "cabbage(local)":               "Cabbage",
    "cabbage (local)":              "Cabbage",
    "cabbage":                      "Cabbage",
    # Onion
    "onion dry(indian)":            "Onion",
    "onion dry (indian)":           "Onion",
    "onion dry(chinese)":           "Onion",
    "onion dry (chinese)":          "Onion",
    # Onion Green
    "onion green(local)":           "Onion Green",
    "onion green (local)":          "Onion Green",
    "onion green":                  "Onion Green",
    # Radish
    "radish(local)":                "Radish",
    "radish (local)":               "Radish",
    "radish":                       "Radish",
    # Spinach
    "spinach(local)":               "Spinach",
    "spinach (local)":              "Spinach",
    "spinach leaf":                 "Spinach",
    # Carrot
    "carrot(local)":                "Carrot",
    "carrot (local)":               "Carrot",
    # Pumpkin
    "pumpkin(local)":               "Pumpkin",
    "pumpkin (local)":              "Pumpkin",
    "pumpkin":                      "Pumpkin",
    # Bitter Gourd
    "bitter gourd(local)":          "Bitter Gourd",
    "bitter gourd (local)":         "Bitter Gourd",
    "bitter gourd":                 "Bitter Gourd",
    # Snake Gourd
    "snake gourd(local)":           "Snake Gourd",
    "snake gourd (local)":          "Snake Gourd",
    "snake gourd":                  "Snake Gourd",
    # Beans
    "beans(local)":                 "Beans",
    "beans (local)":                "Beans",
    "french bean(local)":           "Beans",
    "french bean(hybrid)":          "Beans",
    # Cucumber
    "cucumber(local)":              "Cucumber",
    "cucumber (local)":             "Cucumber",
    "cucumber(localcross)":         "Cucumber",
    # Green Peas
    "green peas(local)":            "Green Peas",
    "green peas (local)":           "Green Peas",
    "green peas":                   "Green Peas",
    # Maize Green
    "maize green(local)":           "Maize Green",
    "maize green (local)":          "Maize Green",
    "maize(green)":                 "Maize Green",
    "maize green":                  "Maize Green",
    # Ginger
    "ginger(dry)":                  "Ginger",
    "ginger (dry)":                 "Ginger",
    "ginger":                       "Ginger",
    # Garlic
    "garlic(dry)":                  "Garlic",
    "garlic (dry)":                 "Garlic",
    "garlic dry nepali":            "Garlic",
    "garlic dry chinese":           "Garlic",
}

TARGET_CROPS = sorted(set(COMMODITY_MAP.values()))


def load_raw() -> pd.DataFrame:
    path = RAW_DIR / "kalimati_combined.csv"
    if not path.exists():
        raise FileNotFoundError(f"Run 01_download_data.py first: {path}")
    df = pd.read_csv(path, parse_dates=["Date"])
    df["commodity_key"] = df["Commodity"].str.strip().str.lower()
    df["crop"] = df["commodity_key"].map(COMMODITY_MAP)
    df = df.dropna(subset=["crop"])
    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    return df


def compute_monthly(df: pd.DataFrame) -> pd.DataFrame:
    grp = df.groupby(["crop", "year", "month"])["Average"]
    monthly = grp.agg(
        avg_price="mean",
        min_price="min",
        max_price="max",
        std_price="std",
    ).reset_index()
    monthly["cv"] = (monthly["std_price"] / monthly["avg_price"] * 100).round(2)
    monthly = monthly.drop(columns=["std_price"])
    return monthly


def add_sell_score(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for crop, grp in monthly.groupby("crop"):
        annual_avg = grp.groupby("year")["avg_price"].mean()
        grp = grp.copy()
        grp["annual_avg"] = grp["year"].map(annual_avg)
        grp["sell_score"] = (
            (grp["avg_price"] / grp["annual_avg"]) * 100 *
            (1 - grp["cv"].clip(0, 100) / 100 * 0.5)
        ).clip(0, 100).round(1)
        rows.append(grp)
    return pd.concat(rows, ignore_index=True)


def add_yoy_change(monthly: pd.DataFrame) -> pd.DataFrame:
    monthly = monthly.sort_values(["crop", "year", "month"])
    monthly["yoy_change"] = monthly.groupby(["crop", "month"])["avg_price"].pct_change() * 100
    monthly["yoy_change"] = monthly["yoy_change"].round(1)
    return monthly


def build_price_json(monthly: pd.DataFrame) -> dict:
    """
    Build the JSON structure consumed by the React frontend.
    {
      "crops": [...],
      "data": {
        "<crop>": {
          "<year>": { "<month>": { avg, min, max, cv, sell_score } }
        }
      },
      "monthly_avg": {
        "<crop>": { "<month>": avg_across_all_years }
      }
    }
    """
    out: dict = {"crops": TARGET_CROPS, "data": {}, "monthly_avg": {}}
    for _, row in monthly.iterrows():
        crop = row["crop"]
        year = str(int(row["year"]))
        month = str(int(row["month"]))
        out["data"].setdefault(crop, {}).setdefault(year, {})[month] = {
            "avg": round(float(row["avg_price"]), 1),
            "min": round(float(row["min_price"]), 1),
            "max": round(float(row["max_price"]), 1),
            "cv": round(float(row["cv"]) if pd.notna(row["cv"]) else 0, 1),
            "sell_score": round(float(row["sell_score"]) if pd.notna(row["sell_score"]) else 50, 1),
        }

    # multi-year monthly averages for the calendar scoring
    for crop, cgrp in monthly.groupby("crop"):
        mo_avg = cgrp.groupby("month")["sell_score"].mean().round(1)
        out["monthly_avg"][crop] = {str(k): v for k, v in mo_avg.items()}

    return out


def main():
    print("Loading raw data...")
    df = load_raw()
    print(f"  {len(df):,} rows for {df['crop'].nunique()} crops")

    print("Computing monthly aggregates...")
    monthly = compute_monthly(df)
    monthly = add_yoy_change(monthly)
    monthly = add_sell_score(monthly)

    csv_path = PROCESSED_DIR / "kalimati_monthly.csv"
    monthly.to_csv(csv_path, index=False)
    print(f"Saved CSV: {csv_path}  ({len(monthly):,} rows)")

    import json, math

    def sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    price_json = build_price_json(monthly)
    json_path = PROCESSED_DIR / "prices_monthly.json"
    with open(json_path, "w") as f:
        json.dump(sanitize(price_json), f, separators=(",", ":"))
    print(f"Saved JSON: {json_path}")


if __name__ == "__main__":
    main()
