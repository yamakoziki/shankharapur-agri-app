# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Shankharapur Agricultural Price & Crop Planning Support App** — a static React web app for farmers near Kathmandu, Nepal. It visualizes Kalimati market vegetable prices (2013–present) and provides zone-aware crop sowing recommendations driven by historical weather data.

Target region: Shankharapur Municipality, split into three elevation zones (zone keys: `lowland`, `mid`, `highland`):
- **lowland** (~1,425m): Sankhu, Bajrayogini
- **mid** (~1,600m): Lapsiphedi, Pukhulachhi, Indrayani
- **highland** (~1,800m): Nanglebhare, Karkigaun, Suntol

The full original build specification is in `shankharapur_agri_app_instructions.md`.

---

## Directory Layout

All working code lives under `shankharapur-agri-app/` (nested one level inside this repo root). Run all commands from there.

```
shankharapur-agri-app/          ← cd here before running anything
├── run_pipeline.sh             ← one-shot: runs all 4 scripts + copies JSON to frontend
├── backend/
│   ├── data/raw/               ← kalimati_combined.csv (output of script 01)
│   ├── data/processed/         ← intermediate JSON/CSV outputs of scripts 02–04
│   └── scripts/
│       ├── 01_download_data.py  # fetch & merge Kalimati price CSVs
│       ├── 02_process_prices.py # monthly aggregation + sell_score → prices_monthly.json
│       ├── 03_fetch_weather.py  # Open-Meteo historical + forecast → weather_zones.json, forecast.json
│       └── 04_crop_calendar.py  # sowing score computation → crop_scores.json, crop_meta.json
└── frontend/
    ├── public/data/            ← JSON served at runtime (copied here by run_pipeline.sh)
    ├── src/
    │   ├── DataContext.jsx     ← loads all JSON via fetch(), provides useData() hook
    │   ├── App.jsx             ← three-tab layout (Price Trend / Crop Calendar / Weather)
    │   ├── pages/
    │   │   ├── PriceTrend.jsx
    │   │   ├── CropCalendar.jsx
    │   │   └── WeatherDashboard.jsx
    │   └── components/
    │       ├── ZoneSelector.jsx  ← zone toggle button group
    │       └── ScoreBadge.jsx    ← scoreColor() helper + badge component
    └── vite.config.js          ← base: '/shankharapur-agri-app/'
```

---

## Common Commands

All commands run from within `shankharapur-agri-app/`.

### Full data pipeline (recommended)
```bash
source venv/bin/activate
bash run_pipeline.sh
```
This runs scripts 01–04, then copies JSON to `frontend/public/data/` (including ASCII re-encoding of `crop_meta.json` to work around a Rolldown JSON parser bug with Devanagari Unicode).

### Run individual pipeline steps
```bash
source venv/bin/activate
python3 backend/scripts/01_download_data.py   # ~5 min, hits GitHub API
python3 backend/scripts/02_process_prices.py
python3 backend/scripts/03_fetch_weather.py   # calls Open-Meteo API
python3 backend/scripts/04_crop_calendar.py   # reads processed/ outputs
```
After running scripts manually, copy outputs:
```bash
cp backend/data/processed/{prices_monthly,weather_zones,forecast,crop_scores}.json frontend/public/data/
python3 -c "import json; d=json.load(open('backend/data/processed/crop_meta.json')); json.dump(d,open('frontend/public/data/crop_meta.json','w'),separators=(',',':'),ensure_ascii=True)"
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Vite dev server at localhost:5173
npm run build     # production build → dist/
npm run deploy    # build + push to GitHub Pages via gh-pages
npm run lint
```

### Python environment setup (first time)
```bash
python3 -m venv venv && source venv/bin/activate
pip install pandas requests python-dotenv
```

---

## Data Flow Architecture

The app is entirely static — no backend server at runtime.

1. **Python pipeline** generates JSON from Kalimati CSV + Open-Meteo API → `backend/data/processed/`
2. `run_pipeline.sh` copies those JSON files to `frontend/public/data/`
3. At app startup, `DataContext.jsx` fetches all 5 JSON files via `fetch(BASE_URL + 'data/...')` and exposes them through `useData()`. Pages are blocked behind a loading state until all 5 files resolve.
4. **No page makes its own data fetch** — all data comes from `useData()`.

JSON files in `frontend/src/data/` are stale copies; the app reads from `public/data/` at runtime.

---

## JSON Data Schemas

**`prices_monthly.json`**
```
{
  "crops": ["Beans", "Bitter Gourd", ...],   // sorted list of canonical crop names
  "data": {
    "<crop>": { "<year>": { "<month>": { avg, min, max, cv, sell_score } } }
  },
  "monthly_avg": { "<crop>": { "<month>": <avg_sell_score_across_all_years> } }
}
```
Month and year keys are strings (e.g. `"1"`, `"2025"`).

**`crop_scores.json`**
```
{ "<zone>": { "<crop>": { <month(1-12)>: { score, temp_score, rain_score, price_score, harvest_month, unsuitable_elevation? } } } }
```
Month keys are integers serialized as strings in JSON.

**`weather_zones.json`**
```
{ "<zone>": { "name", "elevation", "monthly_climate": { <month>: { temp_mean, temp_max, temp_min, precip_monthly_avg, et0_monthly_avg, n_days } } } }
```

**`forecast.json`**
```
{ "<zone>": { "name", "daily": { time[], temperature_2m_max[], temperature_2m_min[], precipitation_sum[], weathercode[] } } }
```

**`crop_meta.json`**
```
{ "<crop>": { name_np, growing_days, elevation_max, sowing_months[], temp_opt } }
```
`name_np` contains Devanagari script — always use ASCII-escaped encoding when writing to `public/data/`.

---

## Key Domain Logic

### sell_score (0–100) — in `02_process_prices.py`
```
sell_score = (monthly_avg / annual_avg) × 100 × (1 − CV/100 × 0.5)
```
High score = high price AND low price volatility that month.

### sowing_score (0–100) — in `04_crop_calendar.py`
```
score = price_score×0.60 + temp_score×0.25 + rain_score×0.15
```
- Price score (60%): harvest-month sell_score from `monthly_avg` in `prices_monthly.json`; harvest month = `(sow_month - 1 + growing_days // 30) % 12 + 1`
- Temperature score (25%): 0–100 based on deviation from `temp_opt`, averaged over growing period, clamped to 0 if any month falls outside `[temp_min, temp_max]`
- Rainfall score (15%): `min(100, total_rain / rain_mm_season × 100)`, with 20% penalty if >150% of requirement
- If zone elevation exceeds `elevation_max`, score is 0 with `unsuitable_elevation: true`

### Elevation lapse rate — in `03_fetch_weather.py`
Open-Meteo returns data at its API grid elevation. Applied correction: `−0.65°C per 100m` difference between API elevation and zone target elevation.

### Commodity name normalization — in `02_process_prices.py`
`COMMODITY_MAP` maps ~80 raw Kalimati commodity strings to 20 canonical crop names (after `str.strip().lower()`). Only mapped commodities are kept. `04_crop_calendar.py` has `CROP_REQUIREMENTS` for all 20 of those crops.

---

## Frontend Patterns

- `scoreColor(score)` in `ScoreBadge.jsx` is the single source of truth for the 5-tier color scale (70+/50-69/35-49/20-34/0-19). Import it wherever score colors are needed.
- Zone keys (`lowland`, `mid`, `highland`) are always lowercase throughout the codebase.
- `CURRENT_MONTH = new Date().getMonth() + 1` (1-indexed) is used in all three pages to highlight the current month.
- Mobile layout uses a fixed bottom nav; desktop uses a top tab bar. Both are in `App.jsx`.
- `useData()` returns `{ prices, weatherZones, forecast, cropScores, cropMeta }` — use these exact destructuring keys in page components.
- Charts use **Recharts**: `LineChart` in `PriceTrend.jsx`, `ComposedChart` (Bar + Line) in `WeatherDashboard.jsx`.
- Tailwind CSS v4 is configured via the `@tailwindcss/vite` Vite plugin — there is no `tailwind.config.js`.
- `WeatherDashboard` shows all three zones simultaneously (no zone selector); `CropCalendar` and `PriceTrend` have per-page zone/crop selectors.

---

## Planned Future Features (Phase 2)

- Auto-update via GitHub Actions scraping Kalimati daily prices
- Nepali (Devanagari) UI using i18n + Noto Sans Devanagari
- WhatsApp/SMS price alerts
- WordPress embed for Shankharapur Municipality website
