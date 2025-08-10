'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../layout'
import Link from 'next/link'

interface Chatbot {
  id: number
  name: string
  status: string
  conversations: number
  messages: number
  created_at: string
  model: string
  temperature: number
}

export default function ChatbotsPage() {
  const { user, token } = useAuth()
  const [chatbots, setChatbots] = useState<Chatbot[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newChatbot, setNewChatbot] = useState({
    title: '',
    description: '',
    system_prompt: 'You are a helpful AI assistant.',
    model: 'llama-3.1-8b-instant',
    temperature: 0.3,
    max_tokens: 1000
  })

  useEffect(() => {
    if (token) {
      fetchChatbots()
    }
  }, [token])

  const fetchChatbots = async () => {
    try {
      const response = await fetch('/api/backend/api/chatbots', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setChatbots(data)
      }
    } catch (error) {
      console.error('Error fetching chatbots:', error)
    } finally {
      setLoading(false)
    }
  }

  const createChatbot = async () => {
    try {
      const response = await fetch('/api/backend/api/chatbots', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newChatbot)
      })
      
      if (response.ok) {
        await fetchChatbots()
        setShowCreateForm(false)
        setNewChatbot({
          title: '',
          description: '',
          system_prompt: 'You are a helpful AI assistant.',
          model: 'llama-3.1-8b-instant',
          temperature: 0.3,
          max_tokens: 1000
        })
      }
    } catch (error) {
      console.error('Error creating chatbot:', error)
    }
  }

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <h2>Please log in to manage chatbots</h2>
        <Link href="/login" style={{ color: '#3b82f6', textDecoration: 'none' }}>
          Go to Login →
        </Link>
      </div>
    )
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '48px' }}>Loading chatbots...</div>
  }

  return (
    <div>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '32px'
      }}>
        <div>
          <h1 style={{ 
            fontSize: '32px', 
            fontWeight: '700', 
            margin: '0 0 8px 0'
          }}>
            🤖 Chatbots
          </h1>
          <p style={{ color: '#6b7280', margin: 0 }}>
            Create and manage your AI chatbots
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateForm(true)}
          style={{
            backgroundColor: '#3b82f6',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            border: 'none',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          + Create Chatbot
        </button>
      </div>

      {/* Create Form Modal */}
      {showCreateForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflowY: 'auto'
          }}>
            <h2 style={{ margin: '0 0 24px 0' }}>Create New Chatbot</h2>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Chatbot Name
              </label>
              <input
                type="text"
                value={newChatbot.title}
                onChange={(e) => setNewChatbot({...newChatbot, title: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
                placeholder="e.g., Customer Support Bot"
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Description
              </label>
              <input
                type="text"
                value={newChatbot.description}
                onChange={(e) => setNewChatbot({...newChatbot, description: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
                placeholder="Brief description of the chatbot"
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                System Prompt
              </label>
              <textarea
                value={newChatbot.system_prompt}
                onChange={(e) => setNewChatbot({...newChatbot, system_prompt: e.target.value})}
                rows={4}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
                placeholder="Define how your chatbot should behave..."
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                  Model
                </label>
                <select
                  value={newChatbot.model}
                  onChange={(e) => setNewChatbot({...newChatbot, model: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontSize: '14px'
                  }}
                >
                  <option value="llama-3.1-8b-instant">Llama 3.1 8B</option>
                  <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
                  <option value="gemma-7b-it">Gemma 7B</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                  Temperature: {newChatbot.temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={newChatbot.temperature}
                  onChange={(e) => setNewChatbot({...newChatbot, temperature: parseFloat(e.target.value)})}
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreateForm(false)}
                style={{
                  padding: '10px 20px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  backgroundColor: 'white',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={createChatbot}
                disabled={!newChatbot.title}
                style={{
                  padding: '10px 20px',
                  backgroundColor: newChatbot.title ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: newChatbot.title ? 'pointer' : 'not-allowed'
                }}
              >
                Create Chatbot
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chatbots Grid */}
      {chatbots.length === 0 ? (
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '48px',
          textAlign: 'center',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '16px' }}>🤖</div>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '20px' }}>No chatbots yet</h3>
          <p style={{ color: '#6b7280', marginBottom: '24px' }}>
            Create your first AI chatbot to get started
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              padding: '12px 24px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Create Your First Chatbot
          </button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
          gap: '24px'
        }}>
          {chatbots.map(chatbot => (
            <div key={chatbot.id} style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                  {chatbot.name}
                </h3>
                <span style={{
                  backgroundColor: chatbot.status === 'active' ? '#10b981' : '#6b7280',
                  color: 'white',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: '500'
                }}>
                  {chatbot.status}
                </span>
              </div>

              <div style={{ 
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px',
                marginBottom: '20px',
                fontSize: '14px',
                color: '#6b7280'
              }}>
                <div>
                  <div style={{ fontWeight: '500', color: '#374151' }}>Conversations</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#3b82f6' }}>
                    {chatbot.conversations || 0}
                  </div>
                </div>
                <div>
                  <div style={{ fontWeight: '500', color: '#374151' }}>Messages</div>
                  <div style={{ fontSize: '20px', fontWeight: '600', color: '#10b981' }}>
                    {chatbot.messages || 0}
                  </div>
                </div>
              </div>

              <div style={{ marginBottom: '20px', fontSize: '12px', color: '#6b7280' }}>
                <div>Model: {chatbot.model || 'llama-3.1-8b-instant'}</div>
                <div>Temperature: {chatbot.temperature || 0.3}</div>
                <div>Created: {new Date(chatbot.created_at).toLocaleDateString()}</div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <Link
                  href={`/chatbots/${chatbot.id}`}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px 12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Manage
                </Link>
                <Link
                  href={`/chatbots/${chatbot.id}/knowledge`}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px 12px',
                    backgroundColor: '#10b981',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Knowledge
                </Link>
                <Link
                  href={`/chatbots/${chatbot.id}/test`}
                  style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: '8px 12px',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Test
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}