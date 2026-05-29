#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Activating Python environment ==="
source venv/bin/activate

echo ""
echo "=== Step 1: Download Kalimati price data ==="
python3 backend/scripts/01_download_data.py

echo ""
echo "=== Step 2: Process prices & compute sell scores ==="
python3 backend/scripts/02_process_prices.py

echo ""
echo "=== Step 3: Fetch weather data (Open-Meteo) ==="
python3 backend/scripts/03_fetch_weather.py

echo ""
echo "=== Step 4: Compute crop sowing scores ==="
python3 backend/scripts/04_crop_calendar.py

echo ""
echo "=== Copying data to frontend ==="
cp backend/data/processed/prices_monthly.json  frontend/public/data/
cp backend/data/processed/weather_zones.json   frontend/public/data/
cp backend/data/processed/forecast.json        frontend/public/data/
cp backend/data/processed/crop_scores.json     frontend/public/data/

# Re-encode crop_meta.json with ASCII-escaped Unicode to avoid Rolldown JSON parser bugs
python3 -c "
import json
with open('backend/data/processed/crop_meta.json') as f:
    d = json.load(f)
with open('frontend/public/data/crop_meta.json', 'w') as f:
    json.dump(d, f, separators=(',', ':'), ensure_ascii=True)
"

echo ""
echo "=== Pipeline complete. Run 'cd frontend && npm run dev' to start the app ==="
