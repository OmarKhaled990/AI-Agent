'use client'

import { useState, useEffect, createContext, useContext } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'

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
// Add this to your layout.tsx or chatbots page to debug token sending

export function TokenDebugger() {
  const { token, user } = useAuth()
  
  const testEndpoints = async () => {
    console.clear()
    console.log('🔍 Testing auth endpoints...')
    
    // 1. Test no-auth endpoint
    try {
      const noAuthResponse = await fetch('/api/backend/api/test/no-auth')
      const noAuthData = await noAuthResponse.json()
      console.log('✅ No-auth test:', noAuthData)
    } catch (error) {
      console.log('❌ No-auth test failed:', error)
    }
    
    // 2. Check token in localStorage
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('auth_user')
    console.log('💾 Stored token:', storedToken ? storedToken.substring(0, 20) + '...' : 'None')
    console.log('💾 Stored user:', storedUser)
    console.log('🎯 Context token:', token ? token.substring(0, 20) + '...' : 'None')
    console.log('👤 Context user:', user)
    
    if (!token) {
      console.log('❌ No token available for authenticated requests')
      return
    }
    
    // 3. Test debug chatbots endpoint
    try {
      console.log('🤖 Testing chatbots debug endpoint...')
      const debugResponse = await fetch('/api/backend/api/chatbots/debug', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      console.log('📡 Debug response status:', debugResponse.status)
      const debugData = await debugResponse.json()
      console.log('📋 Debug response:', debugData)
      
    } catch (error) {
      console.log('❌ Debug endpoint failed:', error)
    }
    
    // 4. Test regular chatbots endpoint
    try {
      console.log('🤖 Testing regular chatbots endpoint...')
      const chatbotsResponse = await fetch('/api/backend/api/chatbots', {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      console.log('📡 Chatbots response status:', chatbotsResponse.status)
      
      if (chatbotsResponse.ok) {
        const chatbotsData = await chatbotsResponse.json()
        console.log('✅ Chatbots success:', chatbotsData)
      } else {
        const errorText = await chatbotsResponse.text()
        console.log('❌ Chatbots error:', errorText)
      }
      
    } catch (error) {
      console.log('❌ Chatbots endpoint failed:', error)
    }
  }
  
  return (
    <div style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      background: 'white',
      border: '2px solid #3b82f6',
      borderRadius: '8px',
      padding: '16px',
      zIndex: 9999,
      fontSize: '12px',
      minWidth: '200px'
    }}>
      <h4>🔍 Auth Debug</h4>
      <div>Token: {token ? '✅ Present' : '❌ Missing'}</div>
      <div>User: {user ? `✅ ${user.username}` : '❌ Missing'}</div>
      <button 
        onClick={testEndpoints}
        style={{
          marginTop: '8px',
          padding: '4px 8px',
          backgroundColor: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '10px'
        }}
      >
        Test Endpoints
      </button>
    </div>
  )
}

// Updated AuthProvider with better token handling
function AuthProviderFixed({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check for stored token on mount
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('auth_user')
      
      console.log('🔄 Loading stored auth data...')
      console.log('Token:', storedToken ? 'Found' : 'Not found')
      console.log('User:', storedUser ? 'Found' : 'Not found')
      
      if (storedToken && storedUser) {
        try {
          const parsedUser = JSON.parse(storedUser)
          setToken(storedToken)
          setUser(parsedUser)
          console.log('✅ Auth data loaded successfully')
        } catch (error) {
          console.log('❌ Error parsing stored user data:', error)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('auth_user')
        }
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      console.log('🔐 Attempting login...')
      
      const response = await fetch('/api/backend/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })

      console.log('📡 Login response status:', response.status)

      if (response.ok) {
        const data = await response.json()
        console.log('✅ Login successful:', data)
        
        // Ensure we have both token and user
        if (data.token && data.user) {
          setToken(data.token)
          setUser(data.user)
          
          if (typeof window !== 'undefined') {
            localStorage.setItem('auth_token', data.token)
            localStorage.setItem('auth_user', JSON.stringify(data.user))
            console.log('💾 Auth data stored successfully')
          }
          
          return true
        } else {
          console.log('❌ Invalid response data:', data)
          return false
        }
      } else {
        const errorText = await response.text()
        console.log('❌ Login failed:', errorText)
        return false
      }
    } catch (error) {
      console.error('🚨 Login error:', error)
      return false
    }
  }

  const logout = () => {
    console.log('🚪 Logging out...')
    setToken(null)
    setUser(null)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    }
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
      <TokenDebugger />
    </AuthContext.Provider>
  )
}
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check for stored token on mount
    if (typeof window !== 'undefined') {
      const storedToken = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('auth_user')
      
      if (storedToken && storedUser) {
        setToken(storedToken)
        setUser(JSON.parse(storedUser))
      }
    }
    setIsLoading(false)
  }, [])

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
        if (typeof window !== 'undefined') {
          localStorage.setItem('auth_token', data.token)
          localStorage.setItem('auth_user', JSON.stringify(data.user))
        }
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
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    }
    router.push('/login')
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

function Navigation() {
  const { user, logout } = useAuth()
  const pathname = usePathname()

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: '📊' },
    { href: '/chatbots', label: 'Chatbots', icon: '🤖' },
    { href: '/knowledge', label: 'Knowledge Base', icon: '📚' },
    { href: '/analytics', label: 'Analytics', icon: '📈' },
    { href: '/integrations', label: 'Integrations', icon: '🔗' },
    { href: '/settings', label: 'Settings', icon: '⚙️' },
  ]

  if (!user) return null

  return (
    <nav style={{ 
      borderBottom: '1px solid #e5e7eb', 
      background: 'white',
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          <Link href="/dashboard" style={{ 
            fontSize: '24px', 
            fontWeight: 'bold',
            color: '#1f2937',
            textDecoration: 'none'
          }}>
            🤖 ChatBase Pro
          </Link>
          
          <div style={{ display: 'flex', gap: '24px' }}>
            {navItems.map(item => (
              <Link 
                key={item.href}
                href={item.href}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  color: pathname === item.href ? '#3b82f6' : '#6b7280',
                  backgroundColor: pathname === item.href ? '#eff6ff' : 'transparent',
                  fontWeight: pathname === item.href ? '600' : '400',
                  transition: 'all 0.2s'
                }}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ 
            padding: '8px 12px',
            backgroundColor: '#f3f4f6',
            borderRadius: '6px',
            fontSize: '14px',
            color: '#374151'
          }}>
            {user.name} ({user.role})
          </div>
          <button
            onClick={logout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
        <title>ChatBase Pro - AI Chatbot Platform</title>
      </head>
      <body style={{ 
        fontFamily: 'Inter, system-ui, sans-serif',
        margin: 0,
        backgroundColor: '#f9fafb',
        color: '#111827'
      }}>
        <AuthProvider>
          <Navigation />
          <main style={{ 
            minHeight: 'calc(100vh - 64px)',
            padding: '24px'
          }}>
            <div style={{ 
              maxWidth: '1200px', 
              margin: '0 auto'
            }}>
              {children}
            </div>
          </main>
        </AuthProvider>
      </body>
    </html>
  )
}
