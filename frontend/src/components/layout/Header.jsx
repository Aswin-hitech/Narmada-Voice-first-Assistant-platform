import { useState } from 'react'
import { Sun, Moon } from 'lucide-react'

export default function Header() {
  const [fontSize, setFontSize] = useState(1) // 0=small, 1=normal, 2=large
  const [highContrast, setHighContrast] = useState(false)

  const applyFontSize = (level) => {
    const sizes = { 0: '14px', 1: '16px', 2: '19px' }
    document.documentElement.style.fontSize = sizes[level]
    setFontSize(level)
  }

  const toggleContrast = () => {
    document.documentElement.classList.toggle('high-contrast')
    setHighContrast((v) => !v)
  }

  return (
    <header className="w-full" style={{ background: 'linear-gradient(135deg, #071527 0%, #0f2b54 100%)' }}>
      {/* Top bar */}
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        {/* Logo + title */}
        <div className="flex items-center gap-4">
          {/* Ashoka Chakra SVG */}
          <div className="flex-shrink-0">
            <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="26" cy="26" r="24" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="2"/>
              <circle cx="26" cy="26" r="4" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5"/>
              {Array.from({ length: 24 }).map((_, i) => {
                const angle = (i * 360) / 24
                const rad = (angle * Math.PI) / 180
                const cos = Math.cos(rad)
                const sin = Math.sin(rad)
                const x1 = 26 + 6 * cos
                const y1 = 26 + 6 * sin
                const x2 = 26 + 22 * cos
                const y2 = 26 + 22 * sin
                return (
                  <line
                    key={i}
                    x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke="rgba(255,255,255,0.3)"
                    strokeWidth="1"
                  />
                )
              })}
              <text
                x="26" y="30"
                fontFamily="'Cinzel', Georgia, serif"
                fontSize="18"
                fontWeight="700"
                fill="#f37021"
                textAnchor="middle"
              >
                N
              </text>
            </svg>
          </div>

          <div>
            <h1 className="font-serif text-2xl sm:text-3xl font-bold tracking-widest text-white leading-none">
              NARMADA
            </h1>
            <p className="text-xs text-slate-400 mt-0.5 leading-tight max-w-xs sm:max-w-none">
              Native-language Aptitude Recognition &amp; Mentoring Architecture Driving Advancement
            </p>
          </div>
        </div>

        {/* Government badges */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="px-3 py-1.5 rounded-lg border border-gold/40 bg-gold/10 text-center">
            <div className="text-gold text-xs font-bold leading-tight">SIH 2026</div>
            <div className="text-slate-400 text-[10px]">Smart India Hackathon</div>
          </div>
          <div className="px-3 py-1.5 rounded-lg border border-gov-green-border/40 bg-gov-green-light/10 text-center">
            <div className="text-gov-green text-xs font-bold leading-tight">MoSJE</div>
            <div className="text-slate-400 text-[10px]">Ministry of Social Justice</div>
          </div>
          <div className="px-3 py-1.5 rounded-lg border border-saffron-border/40 bg-saffron-light/10 text-center">
            <div className="text-saffron text-xs font-bold leading-tight">PM-AJAY</div>
            <div className="text-slate-400 text-[10px]">SC Skilling Initiative</div>
          </div>
        </div>
      </div>

      {/* Accessibility bar */}
      <div className="border-t border-navy-light/30">
        <div className="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between gap-4">
          <div className="text-xs text-slate-500 hidden sm:block">
            Accessibility Controls
          </div>
          <div className="flex items-center gap-2 ml-auto">
            <span className="text-xs text-slate-500 mr-1">Font:</span>
            <button
              onClick={() => applyFontSize(0)}
              className={`w-7 h-7 rounded text-xs font-semibold transition-all ${
                fontSize === 0
                  ? 'bg-saffron text-white'
                  : 'bg-navy-light/40 text-slate-400 hover:bg-navy-light/70'
              }`}
              title="Small font"
              aria-label="Small font size"
            >
              A-
            </button>
            <button
              onClick={() => applyFontSize(1)}
              className={`w-7 h-7 rounded text-sm font-semibold transition-all ${
                fontSize === 1
                  ? 'bg-saffron text-white'
                  : 'bg-navy-light/40 text-slate-400 hover:bg-navy-light/70'
              }`}
              title="Normal font"
              aria-label="Normal font size"
            >
              A
            </button>
            <button
              onClick={() => applyFontSize(2)}
              className={`w-7 h-7 rounded text-base font-semibold transition-all ${
                fontSize === 2
                  ? 'bg-saffron text-white'
                  : 'bg-navy-light/40 text-slate-400 hover:bg-navy-light/70'
              }`}
              title="Large font"
              aria-label="Large font size"
            >
              A+
            </button>
            <div className="w-px h-5 bg-navy-light/40 mx-1" />
            <button
              onClick={toggleContrast}
              className={`flex items-center gap-1.5 px-3 h-7 rounded text-xs font-semibold transition-all ${
                highContrast
                  ? 'bg-gold text-navy-darkest'
                  : 'bg-navy-light/40 text-slate-400 hover:bg-navy-light/70'
              }`}
              title="Toggle high contrast"
              aria-pressed={highContrast}
            >
              {highContrast ? <Sun size={13} /> : <Moon size={13} />}
              <span className="hidden sm:inline">High Contrast</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
