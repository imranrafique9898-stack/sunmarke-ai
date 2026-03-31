'use client'

import { useState, useRef } from 'react'

interface VoiceRecorderProps {
  onTranscribe: (text: string) => void
  isLoading: boolean
}

export default function VoiceRecorder({ onTranscribe, isLoading }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const recognitionRef = useRef<any>(null)

  const initSpeechRecognition = () => {
    if (typeof window === 'undefined') return
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) return

    recognitionRef.current = new SpeechRecognition()
    recognitionRef.current.continuous = true
    recognitionRef.current.interimResults = true
    recognitionRef.current.lang = 'en-US'

    recognitionRef.current.onstart = () => setIsRecording(true)

    recognitionRef.current.onresult = (event: any) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          // always append to existing transcript — never reset
          setTranscript((prev) => prev + event.results[i][0].transcript + ' ')
        }
      }
    }

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)
    }

    recognitionRef.current.onend = () => setIsRecording(false)
  }

  const startRecording = async () => {
    // re-init only if not yet created — keeps existing transcript intact
    if (!recognitionRef.current) initSpeechRecognition()
    if (recognitionRef.current) {
      try { recognitionRef.current.start() } catch {}
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorder.current = new MediaRecorder(stream)
      mediaRecorder.current.start()
    } catch (error) {
      console.error('Microphone error:', error)
    }
  }

  const stopListening = () => {
    // Stop speech recognition but keep the transcript for editing
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    if (mediaRecorder.current) {
      mediaRecorder.current.stop()
      mediaRecorder.current.stream.getTracks().forEach((t) => t.stop())
    }
    setIsRecording(false)
  }

  const handleSubmit = () => {
    if (transcript.trim()) {
      onTranscribe(transcript.trim())
      setTranscript('')
    }
  }

  return (
    <div className="w-full bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold mb-4 text-sunmarke-blue">Ask a Question</h2>

      <div className="mb-4">
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Your question will appear here... or type directly"
          className="w-full h-24 p-4 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-sunmarke-blue transition"
          disabled={isRecording}
        />
      </div>

      {isRecording && (
        <div className="mb-4 flex items-center gap-2 text-red-600 font-semibold">
          <div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
          Listening... speak now
        </div>
      )}

      <div className="flex gap-3 flex-wrap">
        {!isRecording ? (
          <button
            onClick={startRecording}
            disabled={isLoading}
            className="px-6 py-3 bg-sunmarke-blue text-white rounded-lg font-semibold hover:bg-blue-900 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            🎤 Start Recording
          </button>
        ) : (
          <button
            onClick={stopListening}
            className="px-6 py-3 bg-red-600 text-white rounded-lg font-semibold hover:bg-red-700"
          >
            ⏹️ Stop Listening
          </button>
        )}

        <button
          onClick={handleSubmit}
          disabled={!transcript.trim() || isLoading}
          className="px-6 py-3 bg-sunmarke-gold text-black rounded-lg font-semibold hover:bg-yellow-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳ Processing...' : '📤 Send Query'}
        </button>

        <button
          onClick={() => setTranscript('')}
          disabled={isLoading || isRecording}
          className="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-400 disabled:cursor-not-allowed"
        >
          🗑️ Clear
        </button>
      </div>

      {typeof window !== 'undefined' &&
        !(window as any).SpeechRecognition &&
        !(window as any).webkitSpeechRecognition && (
          <div className="mt-4 p-3 bg-yellow-100 text-yellow-800 rounded-lg text-sm">
            ⚠️ Speech recognition not supported. Please use Chrome or Edge.
          </div>
        )}
    </div>
  )
}
