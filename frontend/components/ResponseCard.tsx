'use client'

import { useState } from 'react'

interface ResponseCardProps {
  title: string
  response: string
  isLoading: boolean
  icon: string
}

// Render text with markdown links [text](url) as real <a> tags
function renderWithLinks(text: string) {
  const parts = text.split(/(\[([^\]]+)\]\((https?:\/\/[^\)]+)\))/g)
  const elements: React.ReactNode[] = []
  let i = 0
  while (i < parts.length) {
    const part = parts[i]
    if (part && part.startsWith('[') && parts[i + 2]) {
      // matched group: full match, link text, url
      elements.push(
        <a
          key={i}
          href={parts[i + 2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 underline hover:text-blue-800 break-all"
        >
          {parts[i + 1]}
        </a>
      )
      i += 3
    } else if (part && !part.match(/^\[([^\]]+)\]$/) && !part.match(/^https?:\/\//)) {
      elements.push(<span key={i}>{part}</span>)
      i++
    } else {
      i++
    }
  }
  return elements
}

// Split response into lines and render each with link support
function ResponseText({ text }: { text: string }) {
  return (
    <div className="text-gray-700 leading-relaxed text-sm space-y-2">
      {text.split('\n').map((line, idx) => (
        <p key={idx}>{renderWithLinks(line)}</p>
      ))}
    </div>
  )
}

export default function ResponseCard({ title, response, isLoading, icon }: ResponseCardProps) {
  const [isSpeaking, setIsSpeaking] = useState(false)

  const speak = () => {
    if (!response || !('speechSynthesis' in window)) return
    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    // Strip markdown links and bare URLs before speaking
    const textToSpeak = response
      .replace(/\[([^\]]+)\]\(https?:\/\/[^\)]+\)/g, '$1') // [text](url) -> text only
      .replace(/https?:\/\/\S+/g, '')                        // remove bare URLs
      .replace(/\s{2,}/g, ' ')                               // clean up extra spaces
      .trim()

    const utterance = new SpeechSynthesisUtterance(textToSpeak)
    utterance.rate = 1
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(utterance)
    setIsSpeaking(true)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-3xl">{icon}</span>
        <h3 className="text-xl font-bold text-sunmarke-blue">{title}</h3>
      </div>

      <div className="flex-1 overflow-y-auto mb-4 max-h-80">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-48">
            <div className="w-12 h-12 border-4 border-gray-200 border-t-sunmarke-blue rounded-full animate-spin mb-3"></div>
            <p className="text-gray-500 text-sm">Generating response...</p>
          </div>
        ) : response ? (
          <ResponseText text={response} />
        ) : (
          <div className="flex items-center justify-center h-48">
            <p className="text-gray-400 text-center">Submit a query to get a response</p>
          </div>
        )}
      </div>

      {response && !isLoading && (
        <div className="border-t pt-4">
          <button
            onClick={speak}
            className="w-full px-4 py-2 bg-blue-100 text-blue-800 rounded-lg font-semibold hover:bg-blue-200 transition"
          >
            {isSpeaking ? '⏹️ Stop Speaking' : '🔊 Listen to Response'}
          </button>
        </div>
      )}
    </div>
  )
}
