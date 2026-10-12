import { useLanguage, LANGS } from '../../contexts/LanguageContext'
import { Globe } from 'lucide-react'

export default function LanguageSelector({ className = '' }) {
  const { lang, setLang } = useLanguage()

  return (
    <div className={`relative flex items-center gap-2 ${className}`}>
      <Globe size={15} className="text-saffron flex-shrink-0" />
      <select
        value={lang}
        onChange={(e) => setLang(e.target.value)}
        className="appearance-none bg-navy/80 border border-navy-light/60 text-slate-200
                   rounded-lg pl-2 pr-7 py-1.5 text-sm font-medium cursor-pointer
                   hover:border-saffron/60 focus:outline-none focus:border-saffron
                   transition-colors"
        aria-label="Select language"
      >
        {Object.entries(LANGS).map(([code, meta]) => (
          <option key={code} value={code}>
            {meta.native} ({code})
          </option>
        ))}
      </select>
      <div className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 text-xs">
        ▾
      </div>
    </div>
  )
}
