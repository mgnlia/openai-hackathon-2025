'use client'
import { useState, useRef } from 'react'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type AgentResult = { agent: string; result: string | object; status: 'pending' | 'done' | 'error' }
type Doc = { doc_id: string; filename: string; chars: number; domain: string }

const DOMAINS = ['general', 'legal', 'financial', 'medical', 'technical', 'hr']
const AGENT_LABELS: Record<string, string> = {
  summarizer: '📄 Summary',
  action_extractor: '✅ Action Items',
  risk_analyst: '⚠️ Risk Analysis',
}

export default function Home() {
  const [doc, setDoc] = useState<Doc | null>(null)
  const [domain, setDomain] = useState('general')
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [agents, setAgents] = useState<AgentResult[]>([])
  const [question, setQuestion] = useState('')
  const [qaResult, setQaResult] = useState('')
  const [qaLoading, setQaLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('summarizer')
  const fileRef = useRef<HTMLInputElement>(null)

  const upload = async (file: File) => {
    setUploading(true)
    setDoc(null); setAgents([])
    const fd = new FormData()
    fd.append('file', file)
    fd.append('domain', domain)
    const res = await fetch(`${API}/api/documents/upload`, { method: 'POST', body: fd })
    const data = await res.json()
    setDoc(data)
    setUploading(false)
  }

  const analyze = async () => {
    if (!doc) return
    setAnalyzing(true)
    setAgents([
      { agent: 'summarizer', result: '', status: 'pending' },
      { agent: 'action_extractor', result: '', status: 'pending' },
      { agent: 'risk_analyst', result: '', status: 'pending' },
    ])
    const es = new EventSource(`${API}/api/documents/analyze/stream?doc_id=${encodeURIComponent(doc.doc_id)}&domain=${domain}`)
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'agent_start') {
        setAgents(prev => prev.map(a => a.agent === msg.agent ? { ...a, status: 'pending' } : a))
      } else if (msg.type === 'agent_done') {
        setAgents(prev => prev.map(a => a.agent === msg.agent ? { ...a, result: msg.result, status: 'done' } : a))
        setActiveTab(msg.agent)
      } else if (msg.type === 'agent_error') {
        setAgents(prev => prev.map(a => a.agent === msg.agent ? { ...a, result: msg.error, status: 'error' } : a))
      } else if (msg.type === 'done') {
        es.close(); setAnalyzing(false)
      }
    }
    es.onerror = () => { es.close(); setAnalyzing(false) }
  }

  const askQuestion = async () => {
    if (!doc || !question.trim()) return
    setQaLoading(true); setQaResult('')
    const res = await fetch(`${API}/api/documents/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_id: doc.doc_id, question }),
    })
    const data = await res.json()
    setQaResult(data.result || '')
    setQaLoading(false)
  }

  const activeAgent = agents.find(a => a.agent === activeTab)

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">🤖 DocAgent</h1>
          <p className="text-xs text-gray-400 mt-0.5">Local-first AI document analyst · gpt-oss-20b + gpt-oss-120b</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full">
          <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
          Powered by Groq · gpt-oss
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Upload zone */}
        <div
          className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
            doc ? 'border-blue-500 bg-blue-500/5' : 'border-gray-700 hover:border-gray-500'
          }`}
          onClick={() => fileRef.current?.click()}
          onDragOver={e => e.preventDefault()}
          onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) upload(f) }}
        >
          <input ref={fileRef} type="file" className="hidden" accept=".pdf,.docx,.doc,.txt"
            onChange={e => { const f = e.target.files?.[0]; if (f) upload(f) }} />
          {uploading ? (
            <p className="text-gray-400 animate-pulse">Extracting text…</p>
          ) : doc ? (
            <div>
              <p className="text-blue-400 font-medium">📄 {doc.filename}</p>
              <p className="text-gray-400 text-sm mt-1">{(doc.chars / 1000).toFixed(1)}K characters extracted</p>
            </div>
          ) : (
            <div>
              <p className="text-4xl mb-3">📂</p>
              <p className="text-gray-300 font-medium">Drop a document here</p>
              <p className="text-gray-500 text-sm mt-1">PDF, DOCX, or TXT · max 10MB</p>
            </div>
          )}
        </div>

        {/* Controls */}
        {doc && (
          <div className="flex items-center gap-3">
            <select
              value={domain}
              onChange={e => setDomain(e.target.value)}
              className="bg-gray-800 text-gray-200 rounded-lg px-3 py-2 text-sm border border-gray-700"
            >
              {DOMAINS.map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
            </select>
            <button
              onClick={analyze}
              disabled={analyzing}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              {analyzing ? <><span className="animate-spin">⚙️</span> Analyzing…</> : '🔍 Analyze Document'}
            </button>
          </div>
        )}

        {/* Agent results */}
        {agents.length > 0 && (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 overflow-hidden">
            {/* Tabs */}
            <div className="flex border-b border-gray-800">
              {agents.map(a => (
                <button
                  key={a.agent}
                  onClick={() => setActiveTab(a.agent)}
                  className={`px-4 py-3 text-sm font-medium flex items-center gap-2 transition-colors ${
                    activeTab === a.agent ? 'bg-gray-800 text-white border-b-2 border-blue-500' : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {AGENT_LABELS[a.agent]}
                  {a.status === 'pending' && <span className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />}
                  {a.status === 'done' && <span className="w-2 h-2 bg-green-400 rounded-full" />}
                </button>
              ))}
            </div>
            {/* Content */}
            <div className="p-6 prose prose-invert prose-sm max-w-none">
              {activeAgent?.status === 'pending' && (
                <p className="text-gray-400 animate-pulse">Agent running…</p>
              )}
              {activeAgent?.status === 'done' && (
                typeof activeAgent.result === 'string' ? (
                  <div dangerouslySetInnerHTML={{ __html: activeAgent.result.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                ) : (
                  <pre className="text-xs text-gray-300 overflow-auto">{JSON.stringify(activeAgent.result, null, 2)}</pre>
                )
              )}
            </div>
          </div>
        )}

        {/* Q&A */}
        {doc && (
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-6">
            <h2 className="text-sm font-semibold text-gray-300 mb-3">💬 Ask a Question</h2>
            <div className="flex gap-2">
              <input
                className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
                placeholder="What are the key obligations in this contract?"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && askQuestion()}
              />
              <button
                onClick={askQuestion}
                disabled={qaLoading || !question.trim()}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                {qaLoading ? '…' : 'Ask'}
              </button>
            </div>
            {qaResult && (
              <div className="mt-4 p-4 bg-gray-800 rounded-xl text-sm text-gray-200 leading-relaxed whitespace-pre-wrap">
                {qaResult}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <p className="text-center text-xs text-gray-600">
          OpenAI Open Model Hackathon 2025 · gpt-oss-20b (fast analysis) + gpt-oss-120b (risk analysis) via Groq
        </p>
      </div>
    </main>
  )
}
