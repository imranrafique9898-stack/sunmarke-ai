import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Sunmarke Voice Agent',
  description: 'AI Voice Agent for Sunmarke School Website',
  authors: [{ name: 'XPLServices' }],
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="theme-color" content="#003366" />
      </head>
      <body>
        {children}
      </body>
    </html>
  )
}
