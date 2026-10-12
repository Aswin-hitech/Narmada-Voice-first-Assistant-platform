import { createContext, useContext, useState } from 'react'

const SessionContext = createContext(null)

export function SessionProvider({ children }) {
  const [sessionId, setSessionId] = useState(null)
  const [profile, setProfile] = useState(null)
  const [recommendation, setRecommendation] = useState(null)

  return (
    <SessionContext.Provider
      value={{
        sessionId,
        setSessionId,
        profile,
        setProfile,
        recommendation,
        setRecommendation,
      }}
    >
      {children}
    </SessionContext.Provider>
  )
}

export function useSession() {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within SessionProvider')
  return ctx
}
