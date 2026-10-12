import { createContext, useContext, useState } from 'react'

export const LANGS = {
  'en-IN': { name: 'English (India)', native: 'English', iso: 'en' },
  'hi-IN': { name: 'Hindi', native: 'हिन्दी', iso: 'hi' },
  'ta-IN': { name: 'Tamil', native: 'தமிழ்', iso: 'ta' },
  'te-IN': { name: 'Telugu', native: 'తెలుగు', iso: 'te' },
  'kn-IN': { name: 'Kannada', native: 'ಕನ್ನಡ', iso: 'kn' },
  'ml-IN': { name: 'Malayalam', native: 'മലയാളം', iso: 'ml' },
  'mr-IN': { name: 'Marathi', native: 'मराठी', iso: 'mr' },
  'bn-IN': { name: 'Bengali', native: 'বাংলা', iso: 'bn' },
  'gu-IN': { name: 'Gujarati', native: 'ગુજરાતી', iso: 'gu' },
  'pa-IN': { name: 'Punjabi', native: 'ਪੰਜਾਬੀ', iso: 'pa' },
  'or-IN': { name: 'Odia', native: 'ଓଡ଼ିଆ', iso: 'or' },
}

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('en-IN')

  const langMeta = LANGS[lang] || LANGS['en-IN']

  return (
    <LanguageContext.Provider value={{ lang, setLang, langMeta, LANGS }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
