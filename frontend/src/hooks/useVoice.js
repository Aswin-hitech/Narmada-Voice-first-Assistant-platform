import { useState, useRef, useCallback } from 'react'
import { api } from '../services/api'

export function useVoice() {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [stream, setStream] = useState(null)

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const recognitionRef = useRef(null)

  const startRecording = useCallback(async (langCode = 'en-IN') => {
    setError(null)
    setTranscript('')
    setInterimTranscript('')
    chunksRef.current = []

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      setStream(mediaStream)

      // ── MediaRecorder ──────────────────────────────────────────
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg'

      const recorder = new MediaRecorder(mediaStream, { mimeType })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.start(200)

      // ── Web Speech API for live preview ────────────────────────
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition()
        recognition.lang = langCode
        recognition.continuous = true
        recognition.interimResults = true

        recognition.onresult = (event) => {
          let interim = ''
          let final = ''
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const res = event.results[i]
            if (res.isFinal) {
              final += res[0].transcript + ' '
            } else {
              interim += res[0].transcript
            }
          }
          if (final) setTranscript((prev) => (prev + ' ' + final).trim())
          setInterimTranscript(interim)
        }

        recognition.onerror = (e) => {
          if (e.error !== 'no-speech' && e.error !== 'aborted') {
            console.warn('Speech recognition error:', e.error)
          }
        }

        try {
          recognition.start()
          recognitionRef.current = recognition
        } catch {
          // Recognition may fail on some browsers; MediaRecorder still works
        }
      }

      setIsRecording(true)
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Microphone access denied. Please allow microphone in browser settings.')
      } else if (err.name === 'NotFoundError') {
        setError('No microphone found. Please connect a microphone and try again.')
      } else {
        setError(`Could not start recording: ${err.message}`)
      }
    }
  }, [])

  const stopRecording = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        resolve(null)
        return
      }

      // Stop Web Speech Recognition
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // ignore
        }
        recognitionRef.current = null
      }

      // Stop stream tracks
      if (stream) {
        stream.getTracks().forEach((t) => t.stop())
        setStream(null)
      }

      const recorder = mediaRecorderRef.current
      recorder.onstop = async () => {
        setIsRecording(false)
        setIsProcessing(true)
        setInterimTranscript('')

        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        chunksRef.current = []

        if (blob.size < 500) {
          setIsProcessing(false)
          resolve(transcript || null)
          return
        }

        try {
          const data = await api.transcribe(blob)
          const finalText = data.transcript || data.text || transcript
          setTranscript(finalText)
          setIsProcessing(false)
          resolve(finalText)
        } catch (err) {
          console.warn('ASR transcription failed, using Web Speech result:', err)
          setError('Transcription service unavailable. Using browser speech recognition.')
          setIsProcessing(false)
          resolve(transcript || null)
        }
      }

      if (recorder.state !== 'inactive') {
        recorder.stop()
      } else {
        setIsRecording(false)
        resolve(transcript || null)
      }
    })
  }, [stream, transcript])

  const reset = useCallback(() => {
    setTranscript('')
    setInterimTranscript('')
    setError(null)
    setIsProcessing(false)
  }, [])

  return {
    isRecording,
    isProcessing,
    startRecording,
    stopRecording,
    transcript,
    interimTranscript,
    error,
    stream,
    reset,
  }
}
