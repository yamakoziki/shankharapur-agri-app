export function scoreColor(score) {
  if (score >= 70) return { bg: 'bg-green-500', text: 'text-white', hex: '#22c55e' }
  if (score >= 50) return { bg: 'bg-lime-400', text: 'text-gray-800', hex: '#a3e635' }
  if (score >= 35) return { bg: 'bg-yellow-400', text: 'text-gray-800', hex: '#facc15' }
  if (score >= 20) return { bg: 'bg-orange-400', text: 'text-white', hex: '#fb923c' }
  return { bg: 'bg-red-400', text: 'text-white', hex: '#f87171' }
}

export default function ScoreBadge({ score }) {
  const c = scoreColor(score)
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${c.bg} ${c.text}`}>
      {Math.round(score)}
    </span>
  )
}
