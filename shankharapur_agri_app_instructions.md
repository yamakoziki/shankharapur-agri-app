# Shankharapur農業価格・作付け計画支援アプリ — Claude Code構築指示書

> **対象地域：** Shankharapur Municipality, Kathmandu District, Nepal  
> **目的：** カリマティ市場の農産物価格動向の可視化 + 気象データ連動による年間作付け計画支援  
> **利用者：** カトマンズ近郊農家（スマホ・PC両対応）  
> **言語：** 英語UI（将来的にネパール語対応を想定）

---

## 1. 地域情報（固定パラメータ）

### Shankharapur Municipality 座標・標高区分

| ゾーン | 代表地点 | 緯度 | 経度 | 標高（目安） | 対象地区 |
|--------|----------|------|------|-------------|---------|
| **低地帯 (Lowland)** | Sankhu周辺 | 27.730 | 85.464 | 1,350〜1,500m | Sankhu, Bajrayogini |
| **中標高帯 (Mid-elevation)** | Lapsiphedi周辺 | 27.748 | 85.484 | 1,500〜1,700m | Lapsiphedi, Pukhulachhi, Indrayani |
| **高標高帯 (Highland)** | Sangachok周辺 | 27.762 | 85.506 | 1,700〜1,900m | Nanglebhare, Karkigaun, Suntol |

**市域全体の中心座標：** 27.7504°N, 85.5008°E（面積 60.21 km²）

---

## 2. データソース

### 2-1. 農産物価格データ（Kalimati市場）

| ソース | 期間 | URL / 取得方法 |
|--------|------|---------------|
| Open Data Nepal CSV① | 2013年6月〜2021年5月 | `https://opendatanepal.com/dataset/kalimati-tarkari-dataset` からDL |
| Open Data Nepal CSV② | 2021年5月〜2023年9月 | 同上（別リソース） |
| GitHub ErKiran/kalimati | 2023年〜現在 | `https://github.com/ErKiran/kalimati` （CSVを年/月/日で管理） |
| Kalimati公式サイト | 当日価格 | `https://kalimatimarket.gov.np/` （スクレイピング） |

**CSVカラム構成（Open Data Nepal形式）：**
```
SN, Commodity, Unit, Minimum, Maximum, Average, Date
例: 1, Tomato Big(Nepali), KG, 40, 80, 60, 2023-01-15
```

### 2-2. 気象データ（Open-Meteo API）

**使用するAPI：**

```
# 過去気象データ（ERA5-Land、2013年〜現在）
https://archive-api.open-meteo.com/v1/archive
  ?latitude={lat}&longitude={lon}
  &start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
  &daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,
         precipitation_sum,et0_fao_evapotranspiration
  &timezone=Asia%2FKathmandu

# 14日間予報（現在の天気＋短期予報）
https://api.open-meteo.com/v1/forecast
  ?latitude={lat}&longitude={lon}
  &daily=temperature_2m_max,temperature_2m_min,precipitation_sum,
         weathercode
  &forecast_days=14
  &timezone=Asia%2FKathmandu
```

**3ゾーン分の座標でそれぞれAPIを呼ぶ（標高補正付き）**

---

## 3. アプリ構成（技術スタック）

```
shankharapur-agri-app/
├── backend/
│   ├── data/
│   │   ├── raw/           # ダウンロードした元CSVを格納
│   │   └── processed/
│   │       └── kalimati_monthly.csv   # 月別集計済みデータ
│   ├── scripts/
│   │   ├── 01_download_data.py        # データ取得・結合
│   │   ├── 02_process_prices.py       # 月別集計・スコア計算
│   │   └── 03_fetch_weather.py        # Open-Meteo取得・キャッシュ
│   └── api/
│       └── main.py                    # FastAPI（オプション）
└── frontend/
    ├── index.html
    ├── src/
    │   ├── App.jsx
    │   ├── pages/
    │   │   ├── PriceTrend.jsx         # 価格動向ページ
    │   │   ├── CropCalendar.jsx       # 作付けカレンダーページ
    │   │   └── WeatherDashboard.jsx   # 気象ダッシュボード
    │   └── components/
    │       ├── ZoneSelector.jsx       # 標高ゾーン選択
    │       ├── CropSelector.jsx       # 作物選択
    │       ├── PriceChart.jsx         # 価格チャート
    │       └── CalendarGrid.jsx       # 作付けカレンダー
    ├── package.json
    └── vite.config.js
```

**推奨スタック：**
- Frontend: React + Vite + Tailwind CSS + Recharts（グラフ）
- Backend/データ処理: Python 3.11 + pandas + requests
- ホスティング: GitHub Pages（静的）または Cloudflare Pages

---

## 4. Step-by-Step 実装手順

---

### STEP 1：プロジェクト初期化

```bash
mkdir shankharapur-agri-app && cd shankharapur-agri-app

# Python環境
python3 -m venv venv && source venv/bin/activate
pip install pandas requests python-dotenv fastapi uvicorn

# Reactフロントエンド
npm create vite@latest frontend -- --template react
cd frontend && npm install
npm install recharts @tanstack/react-query axios tailwindcss
npx tailwindcss init -p
```

---

### STEP 2：価格データの収集・整備

**`backend/scripts/01_download_data.py`を作成：**

```python
"""
Kalimati市場の価格CSVを取得し、backend/data/raw/に保存する
- Open Data Nepal から2本のCSVをダウンロード
- GitHub ErKiran/kalimati から2024〜2025年分のCSVを収集
"""
import requests, pandas as pd, os, time
from pathlib import Path

RAW_DIR = Path("backend/data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Open Data Nepal - 2013〜2021
URL_OLD = "https://opendatanepal.com/dataset/af321d1f-979b-4780-9f87-790413bd2270/resource/[リソースID]/download/kalimati-tarkari-2013-2021.csv"
# Open Data Nepal - 2021〜2023
URL_NEW = "https://opendatanepal.com/dataset/af321d1f-979b-4780-9f87-790413bd2270/resource/9a3b365d-692d-4b94-a6c8-47bd9be5ec03/download/kalimati-tarkari-prices-from-may-2021-to-september-2023.csv"

# GitHub ErKiran/kalimati から2024〜2025年
GITHUB_BASE = "https://raw.githubusercontent.com/ErKiran/kalimati/master/data/csv"
# 例: 2024/01/01.csv 〜 2025/12/31.csv を日次でDL

# ダウンロード後、以下のカラムに統一する:
# Date(YYYY-MM-DD), Commodity, Unit, Minimum, Maximum, Average
```

**`backend/scripts/02_process_prices.py`を作成：**

```python
"""
月別・作物別の価格集計と「販売推奨スコア」を計算する

出力: backend/data/processed/kalimati_monthly.csv
  カラム: commodity, month(1-12), year, avg_price, min_price, max_price,
          cv(変動係数%), yoy_change(前年同月比%), sell_score(0-100)

sell_score計算式:
  sell_score = (月平均価格 / 年間平均価格) × 100 × (1 - CV/100 × 0.5)
  → 高価格かつ価格が安定している月を高スコアとする
"""
import pandas as pd, numpy as np
from pathlib import Path

PROCESSED_DIR = Path("backend/data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CROPS = [
    "Tomato Big(Nepali)", "Tomato Small(Local)", "Potato White(Indian)",
    "Potato Red(Indian)", "Cauliflower(Local)", "Cabbage(Local)",
    "Onion Dry(Indian)", "Onion Green(Local)", "Radish(Local)",
    "Spinach(Local)", "Carrot(Local)", "Pumpkin(Local)",
    "Bitter Gourd(Local)", "Snake Gourd(Local)", "Beans(Local)",
    "Cucumber(Local)", "Green Peas(Local)", "Maize Green(Local)",
    "Ginger(Dry)", "Garlic(Dry)"
]
# 必要に応じてSHANKHARAPUR地域で実際に栽培されている作物に絞る
```

---

### STEP 3：気象データの取得・ゾーン別処理

**`backend/scripts/03_fetch_weather.py`を作成：**

```python
"""
3つの標高ゾーンの気象データをOpen-Meteoから取得する

出力:
  backend/data/processed/weather_lowland.json   (標高〜1500m)
  backend/data/processed/weather_mid.json        (1500〜1700m)
  backend/data/processed/weather_highland.json   (1700m〜)
"""
import requests, json
from pathlib import Path
from datetime import date, timedelta

ZONES = {
    "lowland":  {"lat": 27.730, "lon": 85.464, "name": "Sankhu Area (~1,400m)"},
    "mid":      {"lat": 27.748, "lon": 85.484, "name": "Lapsiphedi Area (~1,550m)"},
    "highland": {"lat": 27.762, "lon": 85.506, "name": "Sangachok Area (~1,750m)"},
}

DAILY_VARS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "et0_fao_evapotranspiration",
])

def fetch_historical(zone_key: str, start_date: str, end_date: str) -> dict:
    z = ZONES[zone_key]
    url = (
        f"https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={z['lat']}&longitude={z['lon']}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily={DAILY_VARS}"
        f"&timezone=Asia%2FKathmandu"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_forecast(zone_key: str) -> dict:
    z = ZONES[zone_key]
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={z['lat']}&longitude={z['lon']}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_sum,weathercode"
        f"&forecast_days=14"
        f"&timezone=Asia%2FKathmandu"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.json()

# 月別気候統計（過去5年分）を計算する関数も追加する
# → 各月の平均気温・降水量・蒸発散量を集計
# → 作付け適性判定に使用
```

---

### STEP 4：作付けカレンダーロジックの実装

**`backend/scripts/04_crop_calendar.py`を作成：**

作付けカレンダーは気象条件 × 価格スコアで「おすすめ度」を導出する。

#### 4-1. 主要作物の栽培要件定義（定数テーブル）

```python
"""
各作物の栽培適性条件を定義する
参考: Nepal Agriculture Research Council(NARC)の栽培基準
"""

CROP_REQUIREMENTS = {
    "Tomato": {
        "name_np": "गोलभेडा",
        "temp_min": 10, "temp_opt": 22, "temp_max": 32,
        "rain_mm_season": 400,       # 栽培期間の必要降水量
        "growing_days": 90,          # 播種〜収穫日数
        "elevation_max": 2000,       # 栽培可能最大標高(m)
        "sowing_months": [1,2,3,8,9], # 推奨播種月（月番号）
    },
    "Potato": {
        "name_np": "आलु",
        "temp_min": 7, "temp_opt": 18, "temp_max": 25,
        "rain_mm_season": 300,
        "growing_days": 80,
        "elevation_max": 3000,
        "sowing_months": [1,2,9,10],
    },
    "Cauliflower": {
        "name_np": "काउली",
        "temp_min": 5, "temp_opt": 17, "temp_max": 25,
        "rain_mm_season": 350,
        "growing_days": 70,
        "elevation_max": 2500,
        "sowing_months": [8,9,10],
    },
    "Cabbage": {
        "name_np": "बन्दा",
        "temp_min": 5, "temp_opt": 15, "temp_max": 22,
        "rain_mm_season": 300,
        "growing_days": 80,
        "elevation_max": 2500,
        "sowing_months": [8,9,10],
    },
    "Spinach": {
        "name_np": "पालुंगो",
        "temp_min": 5, "temp_opt": 16, "temp_max": 24,
        "rain_mm_season": 200,
        "growing_days": 45,
        "elevation_max": 2500,
        "sowing_months": [9,10,11,2,3],
    },
    "Cucumber": {
        "name_np": "काक्रो",
        "temp_min": 18, "temp_opt": 28, "temp_max": 38,
        "rain_mm_season": 400,
        "growing_days": 60,
        "elevation_max": 1800,
        "sowing_months": [3,4,5],
    },
    "Beans": {
        "name_np": "सिमी",
        "temp_min": 10, "temp_opt": 22, "temp_max": 30,
        "rain_mm_season": 350,
        "growing_days": 55,
        "elevation_max": 2200,
        "sowing_months": [3,4,8,9],
    },
    "Radish": {
        "name_np": "मूला",
        "temp_min": 5, "temp_opt": 15, "temp_max": 22,
        "rain_mm_season": 200,
        "growing_days": 40,
        "elevation_max": 2500,
        "sowing_months": [8,9,10,11],
    },
    "Onion": {
        "name_np": "प्याज",
        "temp_min": 10, "temp_opt": 20, "temp_max": 28,
        "rain_mm_season": 250,
        "growing_days": 120,
        "elevation_max": 1800,
        "sowing_months": [10,11,12],
    },
    "Pumpkin": {
        "name_np": "फर्सी",
        "temp_min": 18, "temp_opt": 26, "temp_max": 35,
        "rain_mm_season": 400,
        "growing_days": 90,
        "elevation_max": 1900,
        "sowing_months": [3,4,5],
    },
}
```

#### 4-2. スコア計算ロジック

```python
def calc_sowing_score(crop_key, zone_key, sow_month, weather_monthly, price_monthly):
    """
    播種月・ゾーンに対する「おすすめ度スコア」を0〜100で返す

    score = 気温適性(40%) + 降水適性(20%) + 収穫時価格(40%)

    Parameters:
        weather_monthly: {month: {temp_mean, precip_sum}} (過去5年平均)
        price_monthly:   {commodity: {month: sell_score}}
    """
    req = CROP_REQUIREMENTS[crop_key]
    harvest_month = (sow_month + req["growing_days"] // 30 - 1) % 12 + 1

    # 気温スコア（播種月〜収穫月の平均）
    temp_score = 0
    for m in range(sow_month, sow_month + req["growing_days"] // 30):
        mo = (m - 1) % 12 + 1
        t = weather_monthly.get(zone_key, {}).get(mo, {}).get("temp_mean", 18)
        if req["temp_min"] <= t <= req["temp_max"]:
            opt = req["temp_opt"]
            temp_score += 100 - abs(t - opt) * 3
    temp_score = min(100, temp_score / (req["growing_days"] // 30))

    # 降水スコア（播種月〜収穫月の合計降水量）
    total_rain = sum(
        weather_monthly.get(zone_key, {}).get((sow_month + i - 1) % 12 + 1, {}).get("precip_sum", 0)
        for i in range(req["growing_days"] // 30)
    )
    rain_score = min(100, total_rain / req["rain_mm_season"] * 100)
    if total_rain > req["rain_mm_season"] * 1.5:
        rain_score *= 0.8   # 過剰降水はペナルティ

    # 収穫時価格スコア
    price_score = price_monthly.get(crop_key, {}).get(harvest_month, 50)

    return temp_score * 0.4 + rain_score * 0.2 + price_score * 0.4
```

---

### STEP 5：Reactフロントエンドの実装

#### 5-1. ページ構成

**3タブ構成：**

```
Tab 1: 📊 Price Trend（価格動向）
  - 作物セレクタ（ドロップダウン）
  - 期間セレクタ（過去1年/3年/5年/全期間）
  - 月別平均価格の折れ線グラフ（Recharts LineChart）
  - 「今が売り時か？」インジケータ（現在月のスコアをゲージで表示）
  - 直近14日間の価格予想（過去同月のトレンドから推定）

Tab 2: 🌱 Crop Calendar（作付けカレンダー）
  - 標高ゾーン選択（Lowland / Mid / Highland）
  - 年間カレンダーグリッド（月×作物のヒートマップ）
    - 色: 緑（高スコア）→ 黄 → 赤（非推奨）
    - セルをタップ→ 詳細モーダル（気温・降水・価格スコアの内訳）
  - 「今から始めるなら？」ボタン → 現在月から始められる作物TOP5を表示

Tab 3: 🌤️ Weather（気象情報）
  - 3ゾーンの14日間天気予報カード
  - 月別気候グラフ（気温・降水量の棒+折れ線複合グラフ）
  - 農業アドバイス（降水量が少ない→灌漑注意、気温高め→病害リスク等）
```

#### 5-2. モバイル対応の指針

```
- Tailwind CSS の sm:/md:/lg: ブレークポイントで対応
- タブ切り替えはボトムナビゲーション（スマホ）/ サイドバー（PC）
- カレンダーグリッドはスマホでは縦スクロール対応
- グラフはタッチ操作対応（Recharts標準）
- フォントサイズ: base 16px、最小タップ領域 44px
```

#### 5-3. コンポーネント実装例（CalendarGrid）

```jsx
// src/components/CalendarGrid.jsx
// 月(列) × 作物(行) のヒートマップグリッド
// scoreDataは {crop: {month: score}} の形式

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"];

function ScoreCell({ score, onClick }) {
  const bg = score >= 70 ? "bg-green-500"
           : score >= 45 ? "bg-yellow-400"
           : "bg-red-300";
  return (
    <div
      className={`${bg} rounded text-xs text-center py-1 cursor-pointer 
                  hover:opacity-80 transition-opacity`}
      onClick={onClick}
    >
      {Math.round(score)}
    </div>
  );
}

export default function CalendarGrid({ scoreData, zone }) {
  const [modal, setModal] = useState(null);
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left p-1 w-24">Crop</th>
            {MONTHS.map(m => <th key={m} className="p-1 w-12">{m}</th>)}
          </tr>
        </thead>
        <tbody>
          {Object.entries(scoreData).map(([crop, months]) => (
            <tr key={crop}>
              <td className="p-1 font-medium">{crop}</td>
              {Array.from({length:12},(_,i)=>i+1).map(mo => (
                <td key={mo} className="p-0.5">
                  <ScoreCell
                    score={months[mo] ?? 0}
                    onClick={() => setModal({crop, month: mo, zone})}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {modal && <DetailModal {...modal} onClose={() => setModal(null)} />}
    </div>
  );
}
```

---

### STEP 6：データの静的バンドル（GitHub Pages対応）

バックエンドサーバーを使わず、処理済みデータをJSONとしてフロントに同梱する：

```bash
# データ処理を実行して静的JSONを生成
python3 backend/scripts/01_download_data.py
python3 backend/scripts/02_process_prices.py
python3 backend/scripts/03_fetch_weather.py
python3 backend/scripts/04_crop_calendar.py --output frontend/src/data/

# 生成ファイル:
# frontend/src/data/prices_monthly.json   (月別集計価格)
# frontend/src/data/weather_zones.json    (3ゾーン気候統計)
# frontend/src/data/crop_scores.json      (作物×月×ゾーンのスコア)
# frontend/src/data/forecast.json         (14日間予報)
```

Reactアプリはこれらのローカルjsonをimportして動作するため、**APIキーや外部サーバー不要**でGitHub Pagesに静的デプロイできる。

---

### STEP 7：デプロイ

```bash
# vite.config.jsにbaseを設定
# base: '/shankharapur-agri-app/'

cd frontend
npm run build

# GitHub Pagesへデプロイ（gh-pagesパッケージ使用）
npm install -D gh-pages
# package.jsonに追加:
#   "homepage": "https://{username}.github.io/shankharapur-agri-app",
#   "scripts": { "deploy": "gh-pages -d dist" }

npm run deploy
```

---

## 5. 実装順序（推奨）

```
Phase A（〜1日）: データ基盤
  [A1] STEP1: プロジェクト初期化
  [A2] STEP2: Open Data NepalのCSVダウンロード・クレンジング・月別集計
  [A3] STEP3: Open-Meteoから3ゾーンの気象データ取得・月別統計生成

Phase B（〜2日）: 分析ロジック
  [B1] STEP4: 作物栽培要件テーブル作成・スコア計算実装
  [B2] スコアの妥当性確認（既知の作付けパターンと照合）

Phase C（〜3日）: フロントエンド
  [C1] STEP5-Tab1: 価格動向グラフ（最もシンプル、先に完成させる）
  [C2] STEP5-Tab3: 気象ダッシュボード
  [C3] STEP5-Tab2: 作付けカレンダー（最も複雑、最後に実装）
  [C4] モバイル対応・UX調整

Phase D（〜0.5日）: デプロイ
  [D1] STEP6: 静的JSON生成
  [D2] STEP7: GitHub Pagesデプロイ
```

---

## 6. 注意事項・補足

### データについて
- Open Data NepalのCSVは**品目名の表記ゆれ**が多い（例: "Tomato Big(Nepali)" / "Tomato Big (Nepali)"）。`str.strip().lower()`で正規化すること。
- CSV取得URLは変更される可能性があるため、`opendatanepal.com/dataset/kalimati-tarkari-dataset`で最新URLを確認すること。
- GitHub ErKiran/kalimatiの日次CSVは**カラム名が年によって異なる場合**がある。取得後に確認すること。

### 気象データについて
- Open-Meteo Historical APIは**1日最大10,000リクエスト無料**（要レート制限対応）。
- ERA5-Landは0.1°解像度（約9km）のため、3ゾーン間の差は小さい場合がある。標高補正として**気温逓減率 −0.65℃/100m**を手動で適用することで精度を上げられる。
- 予報データは2週間先まで取得可能。価格予測には含めず、作業計画（農薬散布タイミング等）のヒントとして表示する。

### 将来拡張（Phase 2以降）
- Kalimati公式サイトからのスクレイピングによる**当日価格の自動更新**（GitHub Actionsで定期実行）
- **ネパール語 (Devanagari) 対応**（i18n追加、フォントはNoto Sans Devanagari）
- **WhatsApp/SMS通知**機能（価格が一定以上に上昇したらアラート）
- **Shankharapur MunicipalityのWordPressサイトへの埋め込み**（iframe or ウィジェット化）

---

## 7. 参考リンク

| リソース | URL |
|---------|-----|
| Open Data Nepal (Kalimati) | https://opendatanepal.com/dataset/kalimati-tarkari-dataset |
| GitHub ErKiran/kalimati | https://github.com/ErKiran/kalimati |
| Open-Meteo Historical API | https://open-meteo.com/en/docs/historical-weather-api |
| Open-Meteo Forecast API | https://open-meteo.com/en/docs |
| Kalimati公式市場 | https://kalimatimarket.gov.np/ |
| Shankharapur Municipality | https://www.shankharapurmun.gov.np/en |

---

*作成日: 2026年5月 / RGAD（NPO農業開発研究会）Shankharapur IT地域活性化プロジェクト*
