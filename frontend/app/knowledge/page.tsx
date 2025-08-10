'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '../layout'

interface Document {
  id: number
  name: string
  type: string
  size: number
  status: string
  uploaded_at: string
}

interface Chatbot {
  id: number
  name: string
}

export default function KnowledgePage() {
  const { user, token } = useAuth()
  const [chatbots, setChatbots] = useState<Chatbot[]>([])
  const [selectedChatbot, setSelectedChatbot] = useState<number | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  useEffect(() => {
    if (token) {
      fetchChatbots()
    }
  }, [token])

  useEffect(() => {
    if (selectedChatbot) {
      fetchDocuments()
    }
  }, [selectedChatbot])

  const fetchChatbots = async () => {
    try {
      const response = await fetch('/api/backend/api/chatbots', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setChatbots(data)
        if (data.length > 0) {
          setSelectedChatbot(data[0].id)
        }
      }
    } catch (error) {
      console.error('Error fetching chatbots:', error)
    }
  }

  const fetchDocuments = async () => {
    if (!selectedChatbot) return
    
    setLoading(true)
    try {
      const response = await fetch(`/api/backend/api/chatbots/${selectedChatbot}/knowledge`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents)
      }
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (files: FileList) => {
    if (!selectedChatbot || files.length === 0) return

    setUploading(true)
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      const formData = new FormData()
      formData.append('file', file)

      try {
        const response = await fetch(`/api/backend/api/chatbots/${selectedChatbot}/knowledge/upload`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formData
        })

        if (response.ok) {
          await fetchDocuments() // Refresh the documents list
        }
      } catch (error) {
        console.error('Error uploading file:', error)
      }
    }
    
    setUploading(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    handleFileUpload(e.dataTransfer.files)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981'
      case 'processing': return '#f59e0b' 
      case 'failed': return '#ef4444'
      default: return '#6b7280'
    }
  }

  if (!user) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <h2>Please log in to manage knowledge base</h2>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ 
          fontSize: '32px', 
          fontWeight: '700', 
          margin: '0 0 8px 0'
        }}>
          📚 Knowledge Base
        </h1>
        <p style={{ color: '#6b7280', margin: 0 }}>
          Upload documents to enhance your chatbot's knowledge
        </p>
      </div>

      {/* Chatbot Selection */}
      <div style={{ 
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
      }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '18px' }}>Select Chatbot</h2>
        <select
          value={selectedChatbot || ''}
          onChange={(e) => setSelectedChatbot(Number(e.target.value))}
          style={{
            width: '100%',
            padding: '12px',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        >
          <option value="">Choose a chatbot...</option>
          {chatbots.map(chatbot => (
            <option key={chatbot.id} value={chatbot.id}>
              {chatbot.name}
            </option>
          ))}
        </select>
      </div>

      {selectedChatbot && (
        <>
          {/* Upload Area */}
          <div 
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '32px',
              marginBottom: '24px',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
              border: dragOver ? '2px dashed #3b82f6' : '2px dashed #d1d5db',
              backgroundColor: dragOver ? '#eff6ff' : 'white',
              textAlign: 'center',
              cursor: 'pointer'
            }}
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md,.csv"
              onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
              style={{ display: 'none' }}
            />
            
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>
              {uploading ? 'Uploading...' : 'Upload Documents'}
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '16px' }}>
              Drag and drop files here, or click to browse
            </p>
            <p style={{ fontSize: '12px', color: '#9ca3af' }}>
              Supported formats: PDF, DOCX, TXT, MD, CSV (Max 10MB per file)
            </p>
          </div>

          {/* Documents List */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
          }}>
            <h2 style={{ margin: '0 0 20px 0', fontSize: '18px' }}>
              Uploaded Documents ({documents.length})
            </h2>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '32px', color: '#6b7280' }}>
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px', color: '#6b7280' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📄</div>
                <p>No documents uploaded yet</p>
                <p style={{ fontSize: '14px' }}>
                  Upload your first document to get started
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {documents.map(doc => (
                  <div key={doc.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    backgroundColor: '#fafafa'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{ 
                        fontSize: '24px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '40px',
                        height: '40px',
                        backgroundColor: 'white',
                        borderRadius: '6px'
                      }}>
                        {doc.type === '.pdf' ? '📄' : 
                         doc.type === '.docx' ? '📝' : 
                         doc.type === '.csv' ? '📊' : '📄'}
                      </div>
                      
                      <div>
                        <div style={{ fontWeight: '500', fontSize: '14px', marginBottom: '2px' }}>
                          {doc.name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          {formatFileSize(doc.size)} • {doc.type} • {new Date(doc.uploaded_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '500',
                        color: 'white',
                        backgroundColor: getStatusColor(doc.status)
                      }}>
                        {doc.status}
                      </span>
                      
                      <button
                        style={{
                          padding: '6px 12px',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          backgroundColor: 'white',
                          fontSize: '12px',
                          cursor: 'pointer',
                          color: '#ef4444'
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Knowledge Base Stats */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginTop: '24px'
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                {documents.length}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Total Documents</div>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                {documents.filter(d => d.status === 'completed').length}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Processed</div>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              textAlign: 'center',
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                {documents.filter(d => d.status === 'processing').length}
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>Processing</div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}