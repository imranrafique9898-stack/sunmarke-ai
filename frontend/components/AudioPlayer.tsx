'use client'

import { useRef } from 'react'

interface AudioPlayerProps {
  audioUrl: string | null
  isPlaying?: boolean
}

export default function AudioPlayer({ audioUrl, isPlaying = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)

  if (!audioUrl) {
    return null
  }

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-100 rounded">
      <audio ref={audioRef} src={audioUrl} controls className="flex-1" />
    </div>
  )
}
