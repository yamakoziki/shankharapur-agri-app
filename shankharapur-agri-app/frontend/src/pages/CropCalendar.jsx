import { useState, useMemo } from 'react'
import ZoneSelector from '../components/ZoneSelector'
import { scoreColor } from '../components/ScoreBadge'
import { useData } from '../DataContext'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
const CURRENT_MONTH = new Date().getMonth() + 1

function DetailModal({ crop, month, zone, cropScoresData, cropMetaData, onClose }) {
  const entry = cropScoresData?.[zone]?.[crop]?.[month] || {}
  const meta = cropMetaData?.[crop] || {}
  const monthName = MONTHS[month - 1]
  const harvestName = MONTHS[(entry.harvest_month ?? 1) - 1]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl p-5 max-w-sm w-full shadow-xl" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-start mb-3">
          <div>
            <h3 className="font-bold text-gray-900">{crop}</h3>
            <p className="text-xs text-gray-500">{meta.name_np} · Sow in {monthName}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none cursor-pointer">×</button>
        </div>

        <div className="grid grid-cols-4 gap-2 mb-4">
          {[
            { label: 'Overall', value: entry.score ?? 0 },
            { label: 'Temp 40%', value: entry.temp_score ?? 0 },
            { label: 'Rain 20%', value: entry.rain_score ?? 0 },
            { label: 'Price 40%', value: entry.price_score ?? 0 },
          ].map(item => {
            const c = scoreColor(item.value)
            return (
              <div key={item.label} className={`rounded-xl p-2 text-center ${c.bg}`}>
                <div className={`text-xl font-bold ${c.text}`}>{Math.round(item.value)}</div>
                <div className={`text-xs ${c.text} opacity-80 leading-tight`}>{item.label}</div>
              </div>
            )
          })}
        </div>

        <div className="text-xs text-gray-600 space-y-1 border-t pt-3">
          <div className="flex justify-between"><span>Growing period</span><span className="font-medium">{meta.growing_days ?? '—'} days</span></div>
          <div className="flex justify-between"><span>Harvest in</span><span className="font-medium">{harvestName}</span></div>
          <div className="flex justify-between"><span>Max elevation</span><span className="font-medium">{meta.elevation_max ? `${meta.elevation_max}m` : '—'}</span></div>
          {entry.unsuitable_elevation && (
            <div className="text-red-600 text-xs mt-1">⚠ Elevation too high for this crop</div>
          )}
        </div>
      </div>
    </div>
  )
}

function TopFiveCurrent({ zone, cropScoresData, cropMetaData }) {
  const crops = Object.keys(cropMetaData)
  const ranked = crops
    .map(crop => ({ crop, score: cropScoresData?.[zone]?.[crop]?.[CURRENT_MONTH]?.score ?? 0 }))
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)

  return (
    <div className="bg-green-50 border border-green-200 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-green-800 mb-2">
        Start now — Top crops for {MONTHS[CURRENT_MONTH - 1]}
      </h3>
      <div className="space-y-1.5">
        {ranked.map(({ crop, score }, i) => {
          const meta = cropMetaData[crop] || {}
          const c = scoreColor(score)
          return (
            <div key={crop} className="flex items-center gap-2 text-sm">
              <span className="w-5 text-gray-400 text-xs">{i + 1}.</span>
              <span className="flex-1 font-medium text-gray-800">{crop}</span>
              <span className="text-xs text-gray-400">{meta.name_np}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${c.bg} ${c.text}`}>
                {Math.round(score)}
              </span>
            </div>
          )
        })}
        {ranked.length === 0 && (
          <div className="text-xs text-gray-400">No data available.</div>
        )}
      </div>
    </div>
  )
}

export default function CropCalendar() {
  const { cropScores: cropScoresData, cropMeta: cropMetaData } = useData()
  const [zone, setZone] = useState('mid')
  const [modal, setModal] = useState(null)

  const cropList = useMemo(() => Object.keys(cropMetaData), [cropMetaData])

  return (
    <div className="space-y-4">
      <div>
        <label className="text-xs font-semibold text-gray-600 block mb-1">Elevation Zone</label>
        <ZoneSelector value={zone} onChange={setZone} />
      </div>

      <TopFiveCurrent zone={zone} cropScoresData={cropScoresData} cropMetaData={cropMetaData} />

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-x-auto">
        <div className="p-3 border-b border-gray-100 space-y-2">
          <div>
            <h2 className="text-sm font-semibold text-gray-700">
              Sowing Score Heatmap — <span className="text-green-700">{zone.charAt(0).toUpperCase() + zone.slice(1)}</span>
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Each number is the <strong>sowing score for that month</strong> — how suitable it is to
              plant that crop if you sow in that calendar month.
              Tap any cell for a breakdown.
            </p>
          </div>
          <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-800 leading-relaxed">
            <p className="font-semibold mb-1">How the score is calculated (0–100)</p>
            <ul className="space-y-0.5 list-none">
              <li><span className="font-medium text-blue-900">60% — Harvest-month price</span>: the historical Sell Score of the month when the crop would be ready to harvest (sow month + growing days). Higher = better market price at harvest time.</li>
              <li><span className="font-medium">25% — Temperature fit</span>: how close the growing-season temperature is to the crop's optimum. Drops to 0 if temperature goes outside the crop's min/max range.</li>
              <li><span className="font-medium">15% — Rainfall</span>: total precipitation during the growing period vs the crop's seasonal requirement. A 20 % penalty applies if rainfall exceeds 150 % of the requirement (waterlogging risk).</li>
            </ul>
            <p className="mt-1.5 text-blue-600">
              Blank cells = outside the agronomic sowing window for this crop in Shankharapur.
              Harvest month = sow month + growing days ÷ 30.
            </p>
          </div>
        </div>
        <div className="p-2">
          <table className="w-full text-xs">
            <thead>
              <tr>
                <th className="text-left py-1 px-1 w-28 text-gray-500 font-medium sticky left-0 bg-white">Crop</th>
                {MONTHS.map((m, i) => (
                  <th
                    key={m}
                    className={`py-1 px-0.5 text-center font-medium ${i + 1 === CURRENT_MONTH ? 'text-green-700' : 'text-gray-500'}`}
                  >
                    {m.slice(0, 1)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cropList.map(crop => (
                <tr key={crop} className="hover:bg-gray-50">
                  <td className="py-0.5 px-1 font-medium text-gray-700 sticky left-0 bg-white whitespace-nowrap">{crop}</td>
                  {Array.from({ length: 12 }, (_, i) => i + 1).map(mo => {
                    const entry = cropScoresData?.[zone]?.[crop]?.[mo]
                    const isBlank = entry?.score == null
                    const score = isBlank ? 0 : entry.score
                    const c = scoreColor(score)
                    const isCurrent = mo === CURRENT_MONTH
                    return (
                      <td key={mo} className="py-0.5 px-0.5">
                        {isBlank ? (
                          <div
                            className={`w-full rounded py-0.5 ${isCurrent ? 'bg-gray-200' : 'bg-gray-100'}`}
                            style={{ minWidth: 20, height: 20 }}
                          />
                        ) : (
                          <button
                            title={`${crop} · Sow ${MONTHS[mo - 1]} · Score ${Math.round(score)}`}
                            onClick={() => setModal({ crop, month: mo, zone })}
                            className={`w-full rounded text-center py-0.5 cursor-pointer transition-opacity hover:opacity-80 ${c.bg} ${c.text} ${isCurrent ? 'ring-2 ring-green-600 ring-offset-1' : ''}`}
                            style={{ minWidth: 20 }}
                          >
                            {Math.round(score)}
                          </button>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex gap-3 flex-wrap px-3 pb-3 pt-1 text-xs text-gray-500">
          {[
            { label: '70–100 Excellent', bg: 'bg-green-500' },
            { label: '50–69 Good', bg: 'bg-lime-400' },
            { label: '35–49 Fair', bg: 'bg-yellow-400' },
            { label: '20–34 Poor', bg: 'bg-orange-400' },
            { label: '0–19 Avoid', bg: 'bg-red-400' },
          ].map(l => (
            <span key={l.label} className="flex items-center gap-1">
              <span className={`inline-block w-3 h-3 rounded ${l.bg}`} />
              {l.label}
            </span>
          ))}
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-3 rounded bg-gray-200 border border-gray-300" />
            Not sowing season
          </span>
        </div>
      </div>

      {modal && (
        <DetailModal
          {...modal}
          cropScoresData={cropScoresData}
          cropMetaData={cropMetaData}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  )
}
