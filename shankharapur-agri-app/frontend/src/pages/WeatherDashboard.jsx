import { useMemo } from 'react'
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import { useData } from '../DataContext'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const CURRENT_MONTH = new Date().getMonth() + 1

const WMO_CODES = {
  0: '☀️', 1: '🌤️', 2: '⛅', 3: '☁️',
  45: '🌫️', 48: '🌫️',
  51: '🌦️', 53: '🌦️', 55: '🌦️',
  61: '🌧️', 63: '🌧️', 65: '🌧️',
  71: '🌨️', 73: '🌨️', 75: '❄️',
  80: '🌦️', 81: '⛈️', 82: '⛈️',
  95: '⛈️', 96: '⛈️', 99: '⛈️',
}

function weatherIcon(code) { return WMO_CODES[code] ?? '🌡️' }

function ForecastCard({ zoneKey, forecastData }) {
  const zone = forecastData?.[zoneKey]
  if (!zone?.daily?.time?.length) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">{zoneKey}</h3>
        <p className="text-gray-400 text-xs">No forecast data.</p>
      </div>
    )
  }

  const { time, temperature_2m_max, temperature_2m_min, precipitation_sum, weathercode } = zone.daily
  const days = time.slice(0, 7)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <h3 className="font-semibold text-gray-700 text-sm mb-3">{zone.name}</h3>
      <div className="grid grid-cols-7 gap-1 text-center">
        {days.map((dateStr, i) => {
          const d = new Date(dateStr)
          const dayLabel = d.toLocaleDateString('en', { weekday: 'short' }).slice(0, 2)
          const tmax = temperature_2m_max?.[i]
          const tmin = temperature_2m_min?.[i]
          const rain = precipitation_sum?.[i]
          const code = weathercode?.[i]
          return (
            <div key={dateStr} className="flex flex-col items-center gap-0.5">
              <span className="text-xs text-gray-400">{dayLabel}</span>
              <span className="text-xl">{weatherIcon(code)}</span>
              <span className="text-xs font-medium text-orange-600">{tmax != null ? Math.round(tmax) + '°' : '—'}</span>
              <span className="text-xs text-blue-500">{tmin != null ? Math.round(tmin) + '°' : '—'}</span>
              {rain > 0 && (
                <span className="text-xs text-blue-400">💧{rain < 1 ? '<1' : Math.round(rain)}</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ClimateChart({ zoneKey, weatherZonesData }) {
  const climate = weatherZonesData?.[zoneKey]?.monthly_climate

  const data = useMemo(() => {
    if (!climate) return []
    return MONTHS.map((m, i) => {
      const mo = climate[i + 1] || {}
      return {
        month: m,
        temp: mo.temp_mean ?? null,
        precip: mo.precip_monthly_avg ?? null,
      }
    })
  }, [climate])

  if (!data.length || data.every(d => d.temp == null)) {
    return <p className="text-xs text-gray-400 p-2">No climate data.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="month" tick={{ fontSize: 10 }} />
        <YAxis yAxisId="temp" tick={{ fontSize: 10 }} width={28} unit="°" />
        <YAxis yAxisId="rain" orientation="right" tick={{ fontSize: 10 }} width={36} unit="mm" />
        <Tooltip
          formatter={(v, name) => [
            v != null ? (name === 'temp' ? `${v}°C` : `${v}mm`) : '—',
            name === 'temp' ? 'Mean temp' : 'Monthly rain',
          ]}
          contentStyle={{ fontSize: 11 }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        <Bar yAxisId="rain" dataKey="precip" fill="#93c5fd" name="precip" />
        <Line yAxisId="temp" type="monotone" dataKey="temp" stroke="#f97316" strokeWidth={2} dot={false} name="temp" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function AgriAdvice({ zoneKey, weatherZonesData }) {
  const climate = weatherZonesData?.[zoneKey]?.monthly_climate
  if (!climate) return null

  const mo = climate[CURRENT_MONTH] || {}
  const precip = mo.precip_monthly_avg ?? 0
  const temp = mo.temp_mean ?? 20
  const tips = []

  if (precip < 30) tips.push({ icon: '💧', text: 'Low rainfall — check irrigation needs.' })
  if (precip > 200) tips.push({ icon: '🌊', text: 'High rainfall — watch for waterlogging and fungal disease.' })
  if (temp > 28) tips.push({ icon: '🌡️', text: 'High temperatures — pest and disease pressure likely.' })
  if (temp < 10) tips.push({ icon: '❄️', text: 'Cold temperatures — protect frost-sensitive seedlings.' })
  if (CURRENT_MONTH >= 6 && CURRENT_MONTH <= 9) {
    tips.push({ icon: '🌧️', text: 'Monsoon season — main growing period for warm-season crops.' })
  }
  if (tips.length === 0) tips.push({ icon: '✅', text: 'Conditions look normal for the season.' })

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 mt-3 space-y-1.5">
      <h4 className="text-xs font-semibold text-amber-800">Agricultural Advice — {MONTHS[CURRENT_MONTH - 1]}</h4>
      {tips.map((t, i) => (
        <div key={i} className="flex gap-2 text-xs text-amber-900">
          <span>{t.icon}</span>
          <span>{t.text}</span>
        </div>
      ))}
    </div>
  )
}

const ZONE_KEYS = ['lowland', 'mid', 'highland']

export default function WeatherDashboard() {
  const { weatherZones: weatherZonesData, forecast: forecastData } = useData()

  return (
    <div className="space-y-5">
      <div className="grid md:grid-cols-3 gap-3">
        {ZONE_KEYS.map(zk => (
          <ForecastCard key={zk} zoneKey={zk} forecastData={forecastData} />
        ))}
      </div>

      {ZONE_KEYS.map(zk => {
        const zone = weatherZonesData?.[zk]
        return (
          <div key={zk} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-1">
              {zone?.name || zk} — Monthly Climate
            </h2>
            <p className="text-xs text-gray-400 mb-3">5-year average · ERA5-Land with lapse-rate correction</p>
            <ClimateChart zoneKey={zk} weatherZonesData={weatherZonesData} />
            <AgriAdvice zoneKey={zk} weatherZonesData={weatherZonesData} />
          </div>
        )
      })}
    </div>
  )
}
