import { NavLink } from 'react-router-dom'
import { Mic, Calendar, Shield, BookOpen, BarChart2 } from 'lucide-react'

const TABS = [
  { to: '/', label: 'Citizen Voice Companion', Icon: Mic },
  { to: '/mentor', label: 'Weekly Voice Mentor', Icon: Calendar },
  { to: '/officer', label: 'State Officer Portal', Icon: Shield },
  { to: '/knowledge', label: 'NSQF Knowledge Hub', Icon: BookOpen },
  { to: '/impact', label: 'National Impact', Icon: BarChart2 },
]

export default function TabNav() {
  return (
    <nav
      className="w-full border-b border-navy-light/40 sticky top-0 z-40"
      style={{ background: '#0b1c34' }}
    >
      <div className="max-w-7xl mx-auto px-2 sm:px-4">
        <div className="flex overflow-x-auto no-scrollbar">
          {TABS.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 sm:px-5 py-3.5 text-xs sm:text-sm font-semibold
                 whitespace-nowrap border-b-2 transition-all duration-150 flex-shrink-0
                 ${
                   isActive
                     ? 'border-saffron text-saffron bg-saffron/5'
                     : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-navy-surface'
                 }`
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              <span className="hidden sm:inline">{label}</span>
              <span className="inline sm:hidden">{label.split(' ')[0]}</span>
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  )
}
