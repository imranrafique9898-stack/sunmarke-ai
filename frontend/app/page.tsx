'use client'

import { useState, useEffect } from 'react'
import VoiceRecorder from '@/components/VoiceRecorder'
import ResponseCard from '@/components/ResponseCard'
import { queryBackend, healthCheck, ApiStats, getStats } from '@/utils/api'

interface Responses {
  gemini: string
  deepseek: string
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentQuery, setCurrentQuery] = useState('')
  const [responses, setResponses] = useState<Responses>({
    gemini: '',
    deepseek: '',
  })
  const [stats, setStats] = useState<ApiStats | null>(null)
  const [backendReady, setBackendReady] = useState(false)

  // Check backend health on mount with retries
  useEffect(() => {
    const checkBackend = async () => {
      const maxRetries = 5
      const retryDelayMs = 2000
      let lastError = 'unknown error'

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          await healthCheck()
          setBackendReady(true)
          const currentStats = await getStats()
          setStats(currentStats)
          setError('')
          return
        } catch (err: any) {
          lastError = err?.message || 'Backend check failed'
          setBackendReady(false)
          setError(`Backend is not available. Please start the backend server at http://localhost:8000 (attempt ${attempt}/${maxRetries})`)
          if (attempt < maxRetries) {
            await new Promise((resolve) => setTimeout(resolve, retryDelayMs))
          }
        }
      }

      setError(`Backend is not available after ${maxRetries} attempts. Please start the backend server at http://localhost:8000. Error: ${lastError}`)
    }

    checkBackend()
  }, [])

  const handleTranscribe = async (text: string) => {
    if (!text.trim()) return

    setCurrentQuery(text)
    setIsLoading(true)
    setError('')
    setResponses({ gemini: '', deepseek: '' })

    try {
      const result = await queryBackend(text)

      setResponses({
        gemini: result.responses.gemini,
        deepseek: result.responses.deepseek ?? '',
      })

      // Update stats
      const updatedStats = await getStats()
      setStats(updatedStats)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to get response'
      setError(`Error: ${errorMsg}`)
      console.error('Query error:', err)
    } finally {
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
            Ask questions about Sunmarke School - Get instant answers from 3 different AI models
          </p>

          {/* Backend Status */}
          <div className={`inline-block px-4 py-2 rounded-lg font-semibold ${
            backendReady
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}>
            {backendReady ? '✅ Backend Connected' : '❌ Backend Offline'}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border-2 border-red-400 text-red-800 rounded-lg flex items-start gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <h3 className="font-bold">Error</h3>
              <p>{error}</p>
            </div>
          </div>
        )}

        {/* Voice Recorder */}
        <VoiceRecorder onTranscribe={handleTranscribe} isLoading={isLoading} />

        {/* Current Query */}
        {currentQuery && (
          <div className="bg-blue-50 rounded-lg p-4 mb-6 border-l-4 border-sunmarke-blue">
            <p className="text-sm text-gray-600 mb-2">Your Question:</p>
            <p className="text-lg font-semibold text-sunmarke-blue">{currentQuery}</p>
          </div>
        )}

        {/* Response Cards - 3 Column Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <ResponseCard
            title="Groq (Llama 3.3 70B)"
            response={responses.gemini}
            isLoading={isLoading}
            icon="🟢"
          />
          <ResponseCard
            title="Groq (Gemma2 9B)"
            response={responses.deepseek}
            isLoading={isLoading}
            icon="🟠"
          />
        </div>

        {/* Statistics Section */}
        {stats && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 text-sunmarke-blue">📊 System Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-4xl font-bold text-sunmarke-gold">{stats.documents}</p>
                <p className="text-gray-600 mt-2">Documents Indexed</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-sunmarke-blue">{stats.chunks}</p>
                <p className="text-gray-600 mt-2">Content Chunks</p>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-green-600">{stats.queries_processed}</p>
                <p className="text-gray-600 mt-2">Queries Processed</p>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-600 text-sm">
          <p>🚀 XPLServices AI Technical Assessment | Powered by FastAPI, PGVector & Next.js</p>
          <p className="mt-2">
            Backend: <code className="bg-gray-200 px-2 py-1 rounded">http://localhost:8000</code>
          </p>
        </div>
      </div>
    </main>
  )
}
