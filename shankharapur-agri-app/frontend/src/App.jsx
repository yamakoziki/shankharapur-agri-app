import { useState } from 'react'
import { DataProvider } from './DataContext'
import PriceTrend from './pages/PriceTrend'
import CropCalendar from './pages/CropCalendar'
import WeatherDashboard from './pages/WeatherDashboard'

const TABS = [
  { id: 'price', label: 'Price Trend', icon: '📊' },
  { id: 'calendar', label: 'Crop Calendar', icon: '🌱' },
  { id: 'weather', label: 'Weather', icon: '🌤️' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('price')

  return (
    <DataProvider>
    <div className="flex flex-col min-h-screen">
      <header className="bg-green-800 text-white px-4 py-3 shadow-md">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-lg font-bold leading-tight">
            Shankharapur Agriculture
          </h1>
          <p className="text-green-200 text-xs mt-0.5">
            Kalimati Price & Crop Planning · Kathmandu District
          </p>
        </div>
      </header>

      {/* Desktop tab bar */}
      <nav className="hidden md:flex bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto flex w-full">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                activeTab === tab.id
                  ? 'border-green-700 text-green-800'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <main className="flex-1 max-w-5xl w-full mx-auto px-3 py-4 pb-20 md:pb-4">
        {activeTab === 'price' && <PriceTrend />}
        {activeTab === 'calendar' && <CropCalendar />}
        {activeTab === 'weather' && <WeatherDashboard />}
      </main>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex z-50 shadow-lg">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex flex-col items-center py-2 text-xs transition-colors cursor-pointer ${
              activeTab === tab.id ? 'text-green-700' : 'text-gray-500'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="mt-0.5">{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
    </DataProvider>
  )
}
