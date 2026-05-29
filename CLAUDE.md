# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Shankharapur Agricultural Price & Crop Planning Support App** — a web app for farmers near Kathmandu, Nepal. It visualizes Kalimati market vegetable prices and provides zone-aware crop calendar recommendations driven by weather data.

Target region: Shankharapur Municipality (60.21 km², center: 27.7504°N, 85.5008°E), split into three elevation zones:
- **Lowland** (~1,350–1,500m): Sankhu, Bajrayogini
- **Mid-elevation** (~1,500–1,700m): Lapsiphedi, Pukhulachhi, Indrayani
- **Highland** (~1,700–1,900m): Nanglebhare, Karkigaun, Suntol

The full build specification is in `shankharapur_agri_app_instructions.md`.

---

## Tech Stack

- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **Data processing**: Python 3.11 + pandas + requests
- **Deployment**: Static site (GitHub Pages or Cloudflare Pages) — no backend server required at runtime

---

## Project Structure (to be built)

```
shankharapur-agri-app/
├── backend/
│   ├── data/raw/                        # Downloaded source CSVs
│   ├── data/processed/                  # Aggregated outputs
│   └── scripts/
│       ├── 01_download_data.py          # Fetch & merge Kalimati CSVs
│       ├── 02_process_prices.py         # Monthly aggregation + sell_score
│       ├── 03_fetch_weather.py          # Open-Meteo historical + forecast
│       └── 04_crop_calendar.py          # Sowing score computation → JSON
└── frontend/
    ├── src/
    │   ├── data/                        # Static JSON bundled at build time
    │   │   ├── prices_monthly.json
    │   │   ├── weather_zones.json
    │   │   ├── crop_scores.json
    │   │   └── forecast.json
    │   ├── pages/
    │   │   ├── PriceTrend.jsx
    │   │   ├── CropCalendar.jsx
    │   │   └── WeatherDashboard.jsx
    │   └── components/
    │       ├── ZoneSelector.jsx
    │       ├── CropSelector.jsx
    │       ├── PriceChart.jsx
    │       └── CalendarGrid.jsx
    └── vite.config.js                   # Must set base: '/shankharapur-agri-app/'
```

---

## Common Commands

### Python environment setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install pandas requests python-dotenv fastapi uvicorn
```

### Run data pipeline (in order)
```bash
python3 backend/scripts/01_download_data.py
python3 backend/scripts/02_process_prices.py
python3 backend/scripts/03_fetch_weather.py
python3 backend/scripts/04_crop_calendar.py --output frontend/src/data/
```

### Frontend development
```bash
cd frontend
npm install
npm run dev       # dev server
npm run build     # production build
npm run deploy    # deploy to GitHub Pages (requires gh-pages package)
```

---

## Data Sources

| Source | Coverage | Notes |
|--------|----------|-------|
| Open Data Nepal CSV | 2013–2023 | Two separate CSVs; commodity names have whitespace inconsistencies — normalize with `str.strip().lower()` |
| GitHub ErKiran/kalimati | 2023–present | Daily CSVs; column names vary by year — check after download |
| Kalimati official site | Today's price | Scraping target for future auto-update |
| Open-Meteo Archive API | 2013–present | ERA5-Land, 0.1° resolution (~9km) — apply lapse rate −0.65°C/100m for elevation correction |
| Open-Meteo Forecast API | 14-day forecast | For weather dashboard only; do not use for price prediction |

**CSV schema (unified):** `Date(YYYY-MM-DD), Commodity, Unit, Minimum, Maximum, Average`

---

## Key Domain Logic

### sell_score (0–100)
Computed per commodity per month in `02_process_prices.py`:
```
sell_score = (monthly_avg / annual_avg) × 100 × (1 − CV/100 × 0.5)
```
High score = high price AND stable price in that month.

### sowing_score (0–100)
Computed per crop × zone × sowing month in `04_crop_calendar.py`:
```
score = temp_suitability(40%) + rain_suitability(20%) + harvest_month_sell_score(40%)
```
Harvest month is estimated as `sow_month + growing_days // 30`. Excess rainfall (>150% of seasonal requirement) incurs a 20% penalty.

### Elevation lapse rate
Open-Meteo returns values at grid-point elevation. Apply −0.65°C per 100m difference between API elevation and zone target elevation.

---

## Static Deployment Architecture

The app runs entirely as a static site. The Python pipeline generates JSON files that are bundled directly into the React build — no runtime API calls except for the optional live Kalimati scraper. This allows free hosting on GitHub Pages.

`vite.config.js` must set `base: '/shankharapur-agri-app/'` for GitHub Pages routing.

---

## Crop Requirements Table

Defined in `04_crop_calendar.py` as `CROP_REQUIREMENTS`. Key crops: Tomato, Potato, Cauliflower, Cabbage, Spinach, Cucumber, Beans, Radish, Onion, Pumpkin. Each entry includes `temp_min/opt/max`, `rain_mm_season`, `growing_days`, `elevation_max`, and `sowing_months`.

---

## Planned Future Features (Phase 2)

- Auto-update via GitHub Actions scraping Kalimati daily prices
- Nepali (Devanagari) UI using i18n + Noto Sans Devanagari
- WhatsApp/SMS price alerts
- WordPress embed for Shankharapur Municipality website
