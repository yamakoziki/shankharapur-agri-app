import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { useData } from '../DataContext'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const CURRENT_MONTH = new Date().getMonth() + 1

const PERIOD_OPTIONS = [
  { label: '1 yr', years: 1 },
  { label: '3 yr', years: 3 },
  { label: '5 yr', years: 5 },
  { label: 'All', years: 99 },
]

const YEAR_COLORS = ['#86efac', '#4ade80', '#16a34a', '#14532d', '#bbf7d0']

function SellScoreGauge({ score }) {
  const pct = Math.min(100, Math.max(0, score))
  const color = pct >= 70 ? '#16a34a' : pct >= 45 ? '#ca8a04' : '#dc2626'
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="text-xs text-gray-500 font-medium">Sell Score</div>
      <div className="text-3xl font-bold" style={{ color }}>{Math.round(pct)}</div>
      <div
        className="text-xs font-medium px-2 py-0.5 rounded-full"
        style={{ background: color + '20', color }}
      >
        {pct >= 70 ? 'Good time to sell' : pct >= 45 ? 'Average price' : 'Below average'}
      </div>
      <div className="text-xs text-gray-400">{MONTHS[CURRENT_MONTH - 1]}</div>
    </div>
  )
}

export default function PriceTrend() {
  const { prices: pricesData } = useData()
  const crops = pricesData.crops || []
  const [crop, setCrop] = useState(crops[0] || '')
  const [period, setPeriod] = useState(3)

  const chartData = useMemo(() => {
    if (!crop) return []
    const currentYear = new Date().getFullYear()
    const startYear = currentYear - period
    const cropData = pricesData.data?.[crop] || {}

    const monthlyValues = {}
    for (let m = 1; m <= 12; m++) monthlyValues[m] = []

    const yearLines = {}
    for (let y = startYear; y <= currentYear; y++) {
      const yearData = cropData[String(y)]
      if (!yearData) continue
      yearLines[y] = {}
      for (let m = 1; m <= 12; m++) {
        const v = yearData[String(m)]?.avg
        if (v != null) {
          yearLines[y][m] = v
          monthlyValues[m].push(v)
        }
      }
    }

    return MONTHS.map((label, i) => {
      const m = i + 1
      const row = { month: label }
      for (const [y, vals] of Object.entries(yearLines)) {
        row[`y${y}`] = vals[m] ?? null
      }
      const vals = monthlyValues[m]
      row.avg = vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : null
      return row
    })
  }, [crop, period, pricesData])

  const currentMonthScore = useMemo(() => {
    if (!crop) return 50
    return pricesData.monthly_avg?.[crop]?.[String(CURRENT_MONTH)] ?? 50
  }, [crop, pricesData])

  const yearKeys = useMemo(() => {
    const currentYear = new Date().getFullYear()
    const cropData = pricesData.data?.[crop] || {}
    return Array.from({ length: period }, (_, i) => currentYear - period + 1 + i)
      .filter(y => cropData[String(y)])
  }, [crop, period, pricesData])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-start">
        <div className="flex-1 min-w-48">
          <label className="text-xs font-semibold text-gray-600 block mb-1">Crop</label>
          <select
            value={crop}
            onChange={e => setCrop(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {crops.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-600 block mb-1">Period</label>
          <div className="flex gap-1">
            {PERIOD_OPTIONS.map(p => (
              <button
                key={p.label}
                onClick={() => setPeriod(p.years)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  period === p.years
                    ? 'bg-green-700 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:border-green-500'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 px-5 py-3 shadow-sm">
          <SellScoreGauge score={currentMonthScore} />
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          {crop} — Monthly Average Price (NPR/kg)
        </h2>
        {chartData.length === 0 || yearKeys.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-gray-400 text-sm">
            No price data available for this period.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={40} />
              <Tooltip
                formatter={(v, name) => [v ? `NPR ${v}` : '—', name === 'avg' ? 'Multi-yr avg' : name.replace('y', '')]}
                contentStyle={{ fontSize: 12 }}
              />
              <ReferenceLine
                x={MONTHS[CURRENT_MONTH - 1]}
                stroke="#16a34a"
                strokeDasharray="4 2"
                label={{ value: 'Now', position: 'top', fontSize: 10, fill: '#16a34a' }}
              />
              {yearKeys.map((y, i) => (
                <Line
                  key={y}
                  type="monotone"
                  dataKey={`y${y}`}
                  stroke={YEAR_COLORS[i % YEAR_COLORS.length]}
                  strokeWidth={1.5}
                  dot={false}
                  name={`y${y}`}
                />
              ))}
              <Line type="monotone" dataKey="avg" stroke="#166534" strokeWidth={2.5} dot={false} name="avg" />
            </LineChart>
          </ResponsiveContainer>
        )}
        <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-500">
          {yearKeys.map((y, i) => (
            <span key={y} className="flex items-center gap-1">
              <span className="inline-block w-4 h-0.5 rounded" style={{ background: YEAR_COLORS[i % YEAR_COLORS.length] }} />
              {y}
            </span>
          ))}
          {yearKeys.length > 0 && (
            <span className="flex items-center gap-1">
              <span className="inline-block w-4 h-0.5 rounded bg-green-900" />
              Multi-yr avg
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Sell Score by Month</h2>
        <div className="grid grid-cols-12 gap-1">
          {MONTHS.map((m, i) => {
            const score = Number(pricesData.monthly_avg?.[crop]?.[String(i + 1)] ?? 50)
            const color = score >= 70 ? '#16a34a' : score >= 50 ? '#65a30d' : score >= 35 ? '#ca8a04' : '#dc2626'
            return (
              <div key={m} className="flex flex-col items-center gap-0.5">
                <div
                  className="w-full rounded-t"
                  style={{ height: `${Math.max(4, score * 0.8)}px`, background: color }}
                />
                <span className={`text-xs font-medium ${i + 1 === CURRENT_MONTH ? 'text-green-700 font-bold' : 'text-gray-500'}`}>
                  {m.slice(0, 1)}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
