import { useState, useRef, useCallback, useEffect } from 'react'

export function useTTS() {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [rate, setRate] = useState(1.0)
  const [voices, setVoices] = useState([])
  const utteranceRef = useRef(null)

  useEffect(() => {
    const synth = window.speechSynthesis
    if (!synth) return

    const loadVoices = () => {
      const v = synth.getVoices()
      if (v.length > 0) setVoices(v)
    }

    loadVoices()
    synth.addEventListener('voiceschanged', loadVoices)
    return () => synth.removeEventListener('voiceschanged', loadVoices)
  }, [])

  const getBestVoice = useCallback(
    (langCode) => {
      if (!voices.length) return null
      // langCode e.g. 'hi-IN' → iso prefix 'hi'
      const [prefix] = langCode.split('-')

      // 1. Exact match
      let voice = voices.find((v) => v.lang === langCode)
      if (voice) return voice

      // 2. Prefix match
      voice = voices.find((v) => v.lang.startsWith(prefix))
      if (voice) return voice

      // 3. Fallback — English India
      voice = voices.find((v) => v.lang === 'en-IN')
      if (voice) return voice

      // 4. Any English
      voice = voices.find((v) => v.lang.startsWith('en'))
      return voice || null
    },
    [voices]
  )

  const speak = useCallback(
    (text, langCode = 'en-IN') => {
      const synth = window.speechSynthesis
      if (!synth || !text) return

      synth.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = langCode
      utterance.rate = rate
      utterance.pitch = 1.0
      utterance.volume = 1.0

      const voice = getBestVoice(langCode)
      if (voice) utterance.voice = voice

      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      utterance.onerror = () => setIsSpeaking(false)

      utteranceRef.current = utterance
      synth.speak(utterance)
    },
    [rate, getBestVoice]
  )

  const stop = useCallback(() => {
    const synth = window.speechSynthesis
    if (synth) synth.cancel()
    setIsSpeaking(false)
  }, [])

  const RATE_OPTIONS = [
    { label: 'Slow', value: 0.85 },
    { label: 'Normal', value: 1.0 },
    { label: 'Fast', value: 1.15 },
  ]

  return { speak, stop, isSpeaking, rate, setRate, RATE_OPTIONS }
}
