'use client'

import { useState, useEffect } from 'react'
import VoiceRecorder from '@/components/VoiceRecorder'
import ResponseCard from '@/components/ResponseCard'
import { healthCheck, ApiStats, getStats, streamQuery } from '@/utils/api'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentQuery, setCurrentQuery] = useState('')
  const [groq1, setGroq1] = useState('')
  const [groq2, setGroq2] = useState('')
  const [stats, setStats] = useState<ApiStats | null>(null)
  const [backendReady, setBackendReady] = useState(false)

  useEffect(() => {
    const checkBackend = async () => {
      for (let attempt = 1; attempt <= 5; attempt++) {
        try {
          await healthCheck()
          setBackendReady(true)
          setStats(await getStats())
          setError('')
          return
        } catch (err: any) {
          setBackendReady(false)
          setError(`Backend not available (attempt ${attempt}/5). Start the backend server.`)
          if (attempt < 5) await new Promise((r) => setTimeout(r, 2000))
        }
      }
    }
    checkBackend()
  }, [])

  const handleTranscribe = async (text: string) => {
    if (!text.trim()) return
    setCurrentQuery(text)
    setIsLoading(true)
    setError('')
    setGroq1('')
    setGroq2('')

    try {
      await streamQuery(text, (model, token, done) => {
        if (model === 'groq1') setGroq1((prev) => prev + token)
        if (model === 'groq2') setGroq2((prev) => prev + token)
        if (done && model === 'groq2') {
          setIsLoading(false)
          getStats().then(setStats)
        }
      })
    } catch (err: any) {
      setError(`Error: ${err.message || 'Failed to get response'}`)
      setIsLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 px-4">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-sunmarke-blue mb-3">
            🎓 Sunmarke School Voice Agent
          </h1>
          <p className="text-xl text-gray-700 mb-4">
            Ask questions about Sunmarke School — Get instant answers from 2 AI models
          </p>
          <div className={`inline-block px-4 py-2 rounded-lg font-semibold ${
            backendReady ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {backendReady ? '✅ Backend Connected' : '❌ Backend Offline'}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border-2 border-red-400 text-red-800 rounded-lg flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div><p className="font-bold">Error</p><p>{error}</p></div>
          </div>
        )}

        {/* Voice Recorder */}
        <VoiceRecorder onTranscribe={handleTranscribe} isLoading={isLoading} />

        {/* Current Query */}
        {currentQuery && (
          <div className="bg-blue-50 rounded-lg p-4 mb-6 border-l-4 border-sunmarke-blue">
            <p className="text-sm text-gray-600 mb-1">Your Question:</p>
            <p className="text-lg font-semibold text-sunmarke-blue">{currentQuery}</p>
          </div>
        )}

        {/* Response Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <ResponseCard
            title="Groq — Llama 3.3 70B"
            response={groq1}
            isLoading={isLoading && groq1 === ''}
            icon="🟢"
          />
          <ResponseCard
            title="Groq — Gemma2 9B"
            response={groq2}
            isLoading={isLoading && groq2 === ''}
            icon="🟠"
          />
        </div>

        {/* Stats */}
        {stats && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-sunmarke-blue">📊 System Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
              <div>
                <p className="text-4xl font-bold text-sunmarke-gold">{stats.documents}</p>
                <p className="text-gray-600 mt-2">Documents Indexed</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-sunmarke-blue">{stats.chunks}</p>
                <p className="text-gray-600 mt-2">Content Chunks</p>
              </div>
              <div>
                <p className="text-4xl font-bold text-green-600">{stats.queries_processed}</p>
                <p className="text-gray-600 mt-2">Queries Processed</p>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-600 text-sm">
          <p>🚀 XPLServices AI Technical Assessment | Powered by FastAPI + Next.js</p>
          <p className="mt-2">
            Backend: <code className="bg-gray-200 px-2 py-1 rounded">http://localhost:8000</code>
          </p>
        </div>
      </div>
    </main>
  )
}
