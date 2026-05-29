import { createContext, useContext, useEffect, useState } from 'react'

const DataContext = createContext(null)

const BASE = import.meta.env.BASE_URL

async function loadJSON(name) {
  const r = await fetch(`${BASE}data/${name}`)
  if (!r.ok) throw new Error(`Failed to load ${name}`)
  return r.json()
}

export function DataProvider({ children }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      loadJSON('prices_monthly.json'),
      loadJSON('weather_zones.json'),
      loadJSON('forecast.json'),
      loadJSON('crop_scores.json'),
      loadJSON('crop_meta.json'),
    ])
      .then(([prices, weatherZones, forecast, cropScores, cropMeta]) => {
        setData({ prices, weatherZones, forecast, cropScores, cropMeta })
      })
      .catch(err => setError(err.message))
  }, [])

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen p-8">
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 max-w-md text-sm text-red-700">
          <p className="font-semibold mb-1">Failed to load data</p>
          <p>{error}</p>
          <p className="mt-2 text-xs text-red-500">Run the data pipeline scripts first.</p>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-green-700 text-sm animate-pulse">Loading data…</div>
      </div>
    )
  }

  return <DataContext.Provider value={data}>{children}</DataContext.Provider>
}

export function useData() {
  return useContext(DataContext)
}
