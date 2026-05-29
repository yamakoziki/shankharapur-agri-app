"""
Download Kalimati market price CSVs and merge into a single normalized file.
Sources:
  - Kaggle/GitHub mirror CSV (2013-2021, bundled as single file)
  - GitHub ErKiran/kalimati (2023 onward, daily CSVs)

Output: backend/data/raw/kalimati_combined.csv
Columns: Date, Commodity, Unit, Minimum, Maximum, Average
"""
import requests
import pandas as pd
import time
import io
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Public mirror / alternative source for historical data (2013-2021)
# The original Open Data Nepal URLs have changed; use a Kaggle-mirrored version
HISTORICAL_URLS = [
    # ErKiran's repo also has a combined historical CSV
    "https://raw.githubusercontent.com/ErKiran/kalimati/master/kalimati_tarkari_dataset.csv",
]

GITHUB_REPO = "ErKiran/kalimati"
GITHUB_TREE_URL = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/master?recursive=1"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/master"


def normalize_df(df: pd.DataFrame, fallback_date: str = "") -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    rename = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in ("sn", "s.n.", "s.n", "sr"):
            rename[col] = "SN"
        elif cl in ("commodity", "commodities", "item", "product"):
            rename[col] = "Commodity"
        elif cl in ("unit",):
            rename[col] = "Unit"
        elif cl in ("minimum", "min", "min price", "min_price"):
            rename[col] = "Minimum"
        elif cl in ("maximum", "max", "max price", "max_price"):
            rename[col] = "Maximum"
        elif cl in ("average", "avg", "avg price", "avg_price"):
            rename[col] = "Average"
        elif cl in ("date",):
            rename[col] = "Date"
    df = df.rename(columns=rename)

    required = ["Date", "Commodity", "Unit", "Minimum", "Maximum", "Average"]
    for col in required:
        if col not in df.columns:
            if col == "Date" and fallback_date:
                df["Date"] = fallback_date
            else:
                return pd.DataFrame(columns=required)

    df = df[required].copy()
    df["Commodity"] = df["Commodity"].astype(str).str.strip()
    df["Unit"] = df["Unit"].astype(str).str.strip()
    for col in ["Minimum", "Maximum", "Average"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Average"])
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    return df


def download_historical() -> list[pd.DataFrame]:
    frames = []
    for url in HISTORICAL_URLS:
        print(f"  Trying: {url[:80]}...")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), on_bad_lines="skip")
            df = normalize_df(df)
            if not df.empty:
                frames.append(df)
                print(f"    -> {len(df):,} rows  ({df['Date'].min()} – {df['Date'].max()})")
            else:
                print("    -> empty after normalization")
        except Exception as e:
            print(f"    WARN: {e}")
    return frames


def get_github_csv_paths() -> list[str]:
    """Return all ASCII-path CSV files from the repo tree."""
    print("  Fetching repo tree from GitHub API...")
    try:
        r = requests.get(GITHUB_TREE_URL, timeout=30)
        r.raise_for_status()
        tree = r.json().get("tree", [])
        paths = [
            x["path"] for x in tree
            if x["path"].endswith(".csv")
            and all(ord(c) < 128 for c in x["path"])  # ASCII paths only
            and x["path"].startswith("data/csv/")
        ]
        print(f"  Found {len(paths)} ASCII CSV files")
        return paths
    except Exception as e:
        print(f"  ERROR fetching tree: {e}")
        return []


def download_github_csvs(paths: list[str]) -> list[pd.DataFrame]:
    frames = []
    errors = 0
    for i, path in enumerate(paths):
        # Extract date from path: data/csv/YYYY/MM/DD.csv
        parts = path.replace("data/csv/", "").replace(".csv", "").split("/")
        if len(parts) != 3:
            continue
        fallback_date = f"{parts[0]}-{parts[1]}-{parts[2]}"

        url = f"{GITHUB_RAW_BASE}/{path}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), on_bad_lines="skip")
            df = normalize_df(df, fallback_date)
            if not df.empty:
                frames.append(df)
        except Exception:
            errors += 1

        if (i + 1) % 100 == 0:
            print(f"    {i+1}/{len(paths)} files... ({len(frames)} with data, {errors} errors)")
            time.sleep(0.3)  # gentle throttle every 100 requests

    print(f"    Done: {len(frames)} files with data")
    return frames


def main():
    all_frames = []

    print("=== Phase 1: Historical data ===")
    all_frames.extend(download_historical())

    print("\n=== Phase 2: GitHub ErKiran/kalimati daily CSVs ===")
    paths = get_github_csv_paths()
    if paths:
        all_frames.extend(download_github_csvs(paths))

    if not all_frames:
        print("ERROR: No data downloaded.")
        return

    print("\n=== Merging & deduplicating ===")
    combined = pd.concat(all_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["Date", "Commodity"])
    combined = combined.sort_values("Date")

    out_path = RAW_DIR / "kalimati_combined.csv"
    combined.to_csv(out_path, index=False)
    print(f"Saved: {out_path}")
    print(f"  {len(combined):,} rows  |  {combined['Date'].min()} – {combined['Date'].max()}")
    print(f"  {combined['Commodity'].nunique()} unique commodities")


if __name__ == "__main__":
    main()
