'use client'

import { useState, useRef, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const MODELS = [
  { id: 'openai/gpt-oss-20b', label: 'GPT-OSS 20B', badge: 'Fast · ~1000 tps' },
  { id: 'openai/gpt-oss-120b', label: 'GPT-OSS 120B', badge: 'Powerful · Reasoning' },
]

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState(MODELS[0].id)
  const [loading, setLoading] = useState(false)
  const [modelStatus, setModelStatus] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // Test model access on load
    fetch(`${API_URL}/health/model`)
      .then(r => r.json())
      .then(d => setModelStatus(d.test_result?.status === 'ok' ? '✅ gpt-oss connected via Groq' : '⚠️ Model not reachable'))
      .catch(() => setModelStatus('⚠️ Backend not reachable'))
  }, [])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', content: input }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMessages, model }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.content }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error reaching backend.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex flex-col h-screen max-w-3xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white">
          🤖 gpt-oss Demo
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          OpenAI Open Model Hackathon 2025 — powered by Groq
        </p>
        {modelStatus && (
          <p className="text-xs mt-1 text-green-400">{modelStatus}</p>
        )}
      </div>

      {/* Model selector */}
      <div className="flex gap-2 mb-4">
        {MODELS.map(m => (
          <button
            key={m.id}
            onClick={() => setModel(m.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              model === m.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {m.label}
            <span className="ml-1.5 text-xs opacity-70">{m.badge}</span>
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-16">
            <p className="text-4xl mb-3">🧠</p>
            <p>Start a conversation with <strong className="text-gray-300">gpt-oss</strong></p>
            <p className="text-sm mt-1">131K context · tool use · agentic reasoning</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-sm'
                : 'bg-gray-800 text-gray-100 rounded-bl-sm'
            }`}>
              {msg.role === 'assistant' && (
                <span className="text-xs text-gray-400 block mb-1">gpt-oss</span>
              )}
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-2.5 text-sm text-gray-400">
              <span className="animate-pulse">Thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          className="flex-1 bg-gray-800 text-white rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
          placeholder="Message gpt-oss…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-xl px-5 py-3 text-sm font-medium transition-colors"
        >
          Send
        </button>
      </div>
    </main>
  )
}
