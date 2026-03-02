import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OpenAI Hackathon — gpt-oss Demo',
  description: 'Powered by gpt-oss-20b and gpt-oss-120b via Groq',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-950 text-gray-100">{children}</body>
    </html>
  )
}
