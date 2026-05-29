const ZONES = [
  { id: 'lowland', label: 'Lowland', sub: 'Sankhu ~1,400m' },
  { id: 'mid', label: 'Mid', sub: 'Lapsiphedi ~1,550m' },
  { id: 'highland', label: 'Highland', sub: 'Sangachok ~1,750m' },
]

export default function ZoneSelector({ value, onChange }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {ZONES.map(z => (
        <button
          key={z.id}
          onClick={() => onChange(z.id)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer border ${
            value === z.id
              ? 'bg-green-700 text-white border-green-700'
              : 'bg-white text-gray-700 border-gray-300 hover:border-green-500'
          }`}
        >
          <span className="block">{z.label}</span>
          <span className="block text-xs opacity-75">{z.sub}</span>
        </button>
      ))}
    </div>
  )
}
