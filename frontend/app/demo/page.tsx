'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function DemoChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I\'m your ChatBase Pro demo assistant. Ask me anything about this platform!'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      // Start session if needed
      if (!sessionId) {
        const startResponse = await fetch('/api/backend/api/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Demo User' })
        })
        if (startResponse.ok) {
          const startData = await startResponse.json()
          setSessionId(startData.session_id)
        }
      }

      // Send chat message
      const chatResponse = await fetch('/api/backend/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text: userMessage,
          session_id: sessionId
        })
      })

      if (chatResponse.ok) {
        const chatData = await chatResponse.json()
        setMessages(prev => [...prev, { role: 'assistant', content: chatData.reply }])
      } else {
        throw new Error('Chat API error')
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I\'m having trouble connecting. Make sure the backend server is running at http://localhost:8000'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Navigation */}
      <nav style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: '64px'
        }}>
          <Link href="/" style={{
            fontSize: '24px',
            fontWeight: 'bold',
            color: '#1f2937',
            textDecoration: 'none'
          }}>
            🤖 ChatBase Pro
          </Link>
          <div style={{ display: 'flex', gap: '24px' }}>
            <Link href="/" style={{ 
              padding: '8px 16px',
              borderRadius: '6px',
              textDecoration: 'none',
              color: '#6b7280'
            }}>📊 Dashboard</Link>
            <Link href="/demo" style={{ 
              padding: '8px 16px',
              borderRadius: '6px',
              textDecoration: 'none',
              color: '#3b82f6',
              backgroundColor: '#eff6ff',
              fontWeight: '600'
            }}>🚀 Demo Chat</Link>
          </div>
        </div>
      </nav>

      <main style={{
        minHeight: 'calc(100vh - 64px)',
        padding: '24px',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{
          maxWidth: '800px',
          margin: '0 auto'
        }}>
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <h1 style={{ 
              fontSize: '32px', 
              fontWeight: '700', 
              margin: '0 0 8px 0',
              color: '#111827'
            }}>
              🚀 Demo Chat
            </h1>
            <p style={{ 
              color: '#6b7280', 
              fontSize: '16px',
              margin: 0
            }}>
              Try ChatBase Pro's AI assistant. Ask about features or anything else!
            </p>
          </div>

          {/* Chat Container */}
          <div style={{
            background: 'white',
            borderRadius: '12px',
            height: '600px',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
          }}>
            {/* Messages */}
            <div style={{ 
              flex: 1, 
              overflowY: 'auto', 
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              {messages.map((message, index) => (
                <div key={index} style={{
                  display: 'flex',
                  justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                }}>
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: '16px',
                    backgroundColor: message.role === 'user' ? '#3b82f6' : '#f3f4f6',
                    color: message.role === 'user' ? 'white' : '#111827',
                    fontSize: '14px',
                    lineHeight: '1.5'
                  }}>
                    {message.content}
                  </div>
                </div>
              ))}
              
              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '16px',
                    backgroundColor: '#f3f4f6',
                    color: '#6b7280',
                    fontSize: '14px'
                  }}>
                    Thinking...
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{ 
              padding: '20px',
              borderTop: '1px solid #e5e7eb'
            }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Type your message..."
                  disabled={loading}
                  style={{
                    flex: 1,
                    padding: '12px 16px',
                    border: '1px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: loading || !input.trim() ? '#9ca3af' : '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: loading || !input.trim() ? 'not-allowed' : 'pointer'
                  }}
                >
                  Send
                </button>
              </div>
              
              <div style={{ 
                marginTop: '8px',
                fontSize: '12px',
                color: '#6b7280',
                textAlign: 'center'
              }}>
                Press Enter to send • Backend: http://localhost:8000
              </div>
            </div>
          </div>

          {/* Quick Suggestions */}
          <div style={{ marginTop: '32px' }}>
            <h3 style={{ 
              fontSize: '18px',
              fontWeight: '600',
              margin: '0 0 16px 0',
              color: '#111827',
              textAlign: 'center'
            }}>
              💡 Try these questions:
            </h3>
            
            <div style={{ 
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '12px'
            }}>
              {[
                "What makes ChatBase Pro better?",
                "How do I set up my own chatbot?",
                "What AI models do you support?",
                "Can I self-host this platform?",
                "How much does it cost?",
                "What are the main features?"
              ].map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setInput(suggestion)}
                  style={{
                    padding: '12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    backgroundColor: 'white',
                    color: '#374151',
                    fontSize: '13px',
                    cursor: 'pointer',
                    textAlign: 'left'
                  }}
                >
                  "{suggestion}"
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}