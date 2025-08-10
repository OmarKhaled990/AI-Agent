'use client'

import { useState, useEffect, createContext, useContext } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

// Auth Context
interface User {
  id: number
  username: string
  email: string
  name: string
  role: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<boolean>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch('/api/backend/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      if (response.ok) {
        const data = await response.json()
        setToken(data.token)
        setUser(data.user)
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('auth_user', JSON.stringify(data.user))
        return true
      }
      return false
    } catch (error) {
      console.error('Login error:', error)
      return false
    }
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

// Dashboard Component
interface DashboardStats {
  total_conversations: number
  total_messages: number
  avg_response_time: number
  user_satisfaction: number
  daily_stats: Array<{
    date: string
    conversations: number
    messages: number
  }>
}

interface Chatbot {
  id: number
  name: string
  status: string
  conversations: number
  messages: number
  created_at: string
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [chatbots, setChatbots] = useState<Chatbot[]>([])
  const [loading, setLoading] = useState(true)
  const [showLogin, setShowLogin] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [username, setUsername] = useState('')
  const [isRegister, setIsRegister] = useState(false)

  useEffect(() => {
    // Check for existing auth
    const token = localStorage.getItem('auth_token')
    if (token) {
      fetchDashboardData(token)
    } else {
      setLoading(false)
    }
  }, [])

  const fetchDashboardData = async (authToken?: string) => {
    try {
      const token = authToken || localStorage.getItem('auth_token')
      
      if (token) {
        // Fetch with auth
        const [analyticsRes, chatbotsRes] = await Promise.all([
          fetch('/api/backend/api/analytics/overview', {
            headers: { 'Authorization': `Bearer ${token}` }
          }),
          fetch('/api/backend/api/chatbots', {
            headers: { 'Authorization': `Bearer ${token}` }
          })
        ])

        if (analyticsRes.ok) {
          const analyticsData = await analyticsRes.json()
          setStats(analyticsData)
        }

        if (chatbotsRes.ok) {
          const chatbotsData = await chatbotsRes.json()
          setChatbots(chatbotsData)
        }
      } else {
        // Demo data for unauthenticated users
        setStats({
          total_conversations: 142,
          total_messages: 1205,
          avg_response_time: 1.2,
          user_satisfaction: 4.5,
          daily_stats: []
        })
        
        setChatbots([
          {
            id: 1,
            name: "Customer Support Bot",
            status: "active",
            conversations: 85,
            messages: 642,
            created_at: "2024-01-15"
          },
          {
            id: 2,
            name: "Sales Assistant",
            status: "active", 
            conversations: 57,
            messages: 563,
            created_at: "2024-01-20"
          }
        ])
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const endpoint = isRegister ? '/api/backend/api/auth/register' : '/api/backend/api/auth/login'
      const body = isRegister 
        ? { email, password, name, username }
        : { email, password }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      const data = await response.json()

      if (response.ok) {
        localStorage.setItem('auth_token', data.token)
        localStorage.setItem('auth_user', JSON.stringify(data.user))
        setShowLogin(false)
        fetchDashboardData(data.token)
      } else {
        alert(data.detail || 'Authentication failed')
      }
    } catch (error) {
      alert('Network error. Make sure backend is running.')
    }
  }

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        backgroundColor: '#f9fafb'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
          <div>Loading ChatBase Pro...</div>
        </div>
      </div>
    )
  }

  return (
    <AuthProvider>
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
                color: '#3b82f6',
                backgroundColor: '#eff6ff',
                fontWeight: '600'
              }}>📊 Dashboard</Link>
              <Link href="/chatbots" style={{ 
                padding: '8px 16px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: '#6b7280'
              }}>🤖 Chatbots</Link>
              <Link href="/knowledge" style={{ 
                padding: '8px 16px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: '#6b7280'
              }}>📚 Knowledge Base</Link>
              <Link href="/analytics" style={{ 
                padding: '8px 16px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: '#6b7280'
              }}>📈 Analytics</Link>
              <Link href="/demo" style={{ 
                padding: '8px 16px',
                borderRadius: '6px',
                textDecoration: 'none',
                color: '#6b7280'
              }}>🚀 Demo</Link>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowLogin(true)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Login
              </button>
            </div>
          </div>
        </nav>

        <main style={{
          minHeight: 'calc(100vh - 64px)',
          padding: '24px',
          backgroundColor: '#f9fafb'
        }}>
          <div style={{
            maxWidth: '1200px',
            margin: '0 auto'
          }}>
            {/* Header */}
            <div style={{ marginBottom: '32px' }}>
              <h1 style={{ 
                fontSize: '32px', 
                fontWeight: '700', 
                margin: '0 0 8px 0',
                color: '#111827'
              }}>
                Welcome to ChatBase Pro! 👋
              </h1>
              <p style={{ 
                color: '#6b7280', 
                fontSize: '16px',
                margin: 0
              }}>
                Professional AI chatbot platform with RAG, analytics, and multi-tenancy
              </p>
            </div>

            {/* Quick Stats */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
              gap: '24px',
              marginBottom: '32px'
            }}>
              <StatCard title="Total Conversations" value={stats?.total_conversations || 0} icon="💬" color="#3b82f6" />
              <StatCard title="Total Messages" value={stats?.total_messages || 0} icon="📨" color="#10b981" />
              <StatCard title="Avg Response Time" value={`${stats?.avg_response_time || 0}s`} icon="⚡" color="#f59e0b" />
              <StatCard title="User Satisfaction" value={`${stats?.user_satisfaction || 0}/5`} icon="⭐" color="#ef4444" />
            </div>

            {/* Main Content Grid */}
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '2fr 1fr', 
              gap: '32px',
              alignItems: 'start'
            }}>
              {/* Features List */}
              <div style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
              }}>
                <h2 style={{ 
                  fontSize: '20px', 
                  fontWeight: '600',
                  margin: '0 0 20px 0',
                  color: '#111827'
                }}>
                  🚀 Advanced Features
                </h2>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <FeatureItem 
                    icon="🔐"
                    title="Authentication & Multi-tenancy"
                    description="JWT tokens, organizations, role-based access"
                    status="available"
                  />
                  <FeatureItem 
                    icon="🤖"
                    title="Advanced Chatbot Management"
                    description="Multiple bots, custom prompts, model settings"
                    status="available"
                  />
                  <FeatureItem 
                    icon="📚"
                    title="RAG Knowledge Base"
                    description="PDF/DOCX upload, embeddings, semantic search"
                    status="available"
                  />
                  <FeatureItem 
                    icon="📊"
                    title="Real-time Analytics"
                    description="Conversation metrics, user engagement, exports"
                    status="available"
                  />
                  <FeatureItem 
                    icon="🔗"
                    title="API & Integrations"
                    description="Full REST API, webhooks, embeddable widgets"
                    status="available"
                  />
                  <FeatureItem 
                    icon="🐳"
                    title="Production Ready"
                    description="Docker, rate limiting, background tasks"
                    status="available"
                  />
                </div>
              </div>

              {/* Quick Actions */}
              <div style={{
                background: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
              }}>
                <h2 style={{ 
                  fontSize: '20px', 
                  fontWeight: '600',
                  margin: '0 0 20px 0',
                  color: '#111827'
                }}>
                  🎯 Quick Actions
                </h2>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <ActionButton 
                    href="/demo"
                    icon="🚀"
                    title="Try Demo Chat"
                    description="Test the AI assistant"
                  />
                  <ActionButton 
                    href="/chatbots/new"
                    icon="🤖"
                    title="Create Chatbot"
                    description="Set up a new AI assistant"
                  />
                  <ActionButton 
                    href="/knowledge"
                    icon="📚"
                    title="Upload Documents"
                    description="Add knowledge with RAG"
                  />
                  <ActionButton 
                    href="/analytics"
                    icon="📊"
                    title="View Analytics"
                    description="Detailed metrics"
                  />
                </div>
              </div>
            </div>

            {/* Chatbots List */}
            <div style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
              marginTop: '32px'
            }}>
              <h2 style={{ 
                fontSize: '20px', 
                fontWeight: '600',
                margin: '0 0 20px 0',
                color: '#111827'
              }}>
                🤖 Your Chatbots
              </h2>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {chatbots.map(chatbot => (
                  <div key={chatbot.id} style={{
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <h3 style={{ 
                        margin: '0 0 4px 0',
                        fontSize: '16px',
                        fontWeight: '600'
                      }}>
                        {chatbot.name}
                      </h3>
                      <div style={{ 
                        display: 'flex', 
                        gap: '16px',
                        fontSize: '14px',
                        color: '#6b7280'
                      }}>
                        <span>💬 {chatbot.conversations} conversations</span>
                        <span>📨 {chatbot.messages} messages</span>
                        <span style={{
                          backgroundColor: '#10b981',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          {chatbot.status}
                        </span>
                      </div>
                    </div>
                    <Link 
                      href={`/chatbots/${chatbot.id}`}
                      style={{
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        textDecoration: 'none',
                        fontSize: '14px',
                        fontWeight: '500'
                      }}
                    >
                      Manage →
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>

        {/* Login Modal */}
        {showLogin && (
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
              background: 'white',
              borderRadius: '12px',
              padding: '32px',
              width: '400px',
              maxWidth: '90vw'
            }}>
              <h2 style={{ 
                fontSize: '24px',
                fontWeight: '600',
                margin: '0 0 20px 0',
                textAlign: 'center'
              }}>
                {isRegister ? 'Create Account' : 'Sign In'}
              </h2>
              
              <form onSubmit={handleAuth}>
                {isRegister && (
                  <>
                    <input
                      type="text"
                      placeholder="Full Name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        marginBottom: '12px',
                        fontSize: '14px'
                      }}
                    />
                    <input
                      type="text"
                      placeholder="Username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      style={{
                        width: '100%',
                        padding: '12px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        marginBottom: '12px',
                        fontSize: '14px'
                      }}
                    />
                  </>
                )}
                
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    marginBottom: '12px',
                    fontSize: '14px'
                  }}
                />
                
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    marginBottom: '16px',
                    fontSize: '14px'
                  }}
                />
                
                <button
                  type="submit"
                  style={{
                    width: '100%',
                    padding: '12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '14px',
                    fontWeight: '600',
                    marginBottom: '12px',
                    cursor: 'pointer'
                  }}
                >
                  {isRegister ? 'Create Account' : 'Sign In'}
                </button>
              </form>
              
              <div style={{ textAlign: 'center' }}>
                <button
                  onClick={() => setIsRegister(!isRegister)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#3b82f6',
                    fontSize: '14px',
                    cursor: 'pointer',
                    marginRight: '16px'
                  }}
                >
                  {isRegister ? 'Sign In Instead' : 'Create Account'}
                </button>
                
                <button
                  onClick={() => setShowLogin(false)}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#6b7280',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AuthProvider>
  )
}

// Helper Components
function StatCard({ title, value, icon, color }: {
  title: string
  value: string | number
  icon: string
  color: string
}) {
  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '24px',
      boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      border: `2px solid ${color}20`
    }}>
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        marginBottom: '8px'
      }}>
        <span style={{ fontSize: '24px' }}>{icon}</span>
        <div style={{
          backgroundColor: `${color}20`,
          borderRadius: '50%',
          width: '12px',
          height: '12px'
        }} />
      </div>
      <div style={{ 
        fontSize: '32px', 
        fontWeight: '700',
        color: color,
        marginBottom: '4px'
      }}>
        {value}
      </div>
      <div style={{ 
        fontSize: '14px', 
        color: '#6b7280',
        fontWeight: '500'
      }}>
        {title}
      </div>
    </div>
  )
}

function FeatureItem({ icon, title, description, status }: {
  icon: string
  title: string
  description: string
  status: 'available' | 'coming-soon'
}) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      padding: '12px',
      border: '1px solid #e5e7eb',
      borderRadius: '8px'
    }}>
      <span style={{ fontSize: '24px' }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <div style={{ 
          fontWeight: '600',
          fontSize: '14px',
          marginBottom: '2px'
        }}>
          {title}
        </div>
        <div style={{ 
          fontSize: '12px',
          color: '#6b7280'
        }}>
          {description}
        </div>
      </div>
      <div style={{
        backgroundColor: status === 'available' ? '#10b981' : '#f59e0b',
        color: 'white',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: '600'
      }}>
        {status === 'available' ? '✓ Available' : 'Coming Soon'}
      </div>
    </div>
  )
}

function ActionButton({ href, icon, title, description }: {
  href: string
  icon: string
  title: string
  description: string
}) {
  return (
    <Link href={href} style={{
      display: 'block',
      padding: '16px',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      textDecoration: 'none',
      color: 'inherit',
      transition: 'all 0.2s'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '24px' }}>{icon}</span>
        <div>
          <div style={{ 
            fontWeight: '600',
            fontSize: '14px',
            marginBottom: '2px'
          }}>
            {title}
          </div>
          <div style={{ 
            fontSize: '12px',
            color: '#6b7280'
          }}>
            {description}
          </div>
        </div>
      </div>
    </Link>
  )
}