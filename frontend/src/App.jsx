
import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hello! I am your Enterprise AI Employee Assistant. Ask me about HR, payroll, leave balances, or upload a PDF.',
    },
  ])
  const [loading, setLoading] = useState(false)
  const [employeeId, setEmployeeId] = useState('EMP001')
  const [file, setFile] = useState(null)

  async function sendMessage(event) {
    event.preventDefault()
    const text = question.trim()
    if (!text || loading) return

    setMessages((previous) => [...previous, { role: 'user', text }])
    setQuestion('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text }),
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: data.answer || 'No answer returned.',
          agent: data.agent,
          tool: data.tool,
          sources: data.sources || [],
        },
      ])
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: 'Could not connect to FastAPI. Make sure your backend is running. If it is running, we may need to enable CORS in app.py.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  async function uploadPDF(event) {
    event.preventDefault()
    if (!file) {
      alert('Please choose a PDF first.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://127.0.0.1:8000/upload-pdf', {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || 'Upload failed')

      setMessages((previous) => [
        ...previous,
        {
          role: 'assistant',
          text: data.message || 'PDF uploaded successfully.',
        },
      ])
      setFile(null)
      event.target.reset()
    } catch (error) {
      alert(`Upload failed: ${error.message}`)
    }
  }

  const suggestions = [
    'How does payroll work?',
    'What is the leave policy?',
    'Who can help with HR questions?',
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">E</div>
          <div>
            <h2>Enterprise AI</h2>
            <p>Employee Assistant</p>
          </div>
        </div>

        <button
          className="new-chat"
          onClick={() =>
            setMessages([
              {
                role: 'assistant',
                text: 'New conversation started. How can I help?',
              },
            ])
          }
        >
          ＋ New conversation
        </button>

        <div className="sidebar-section">
          <p className="section-label">WORKSPACE</p>
          <div className="nav-item active">◈ &nbsp; AI Assistant</div>
          <div className="nav-item">▤ &nbsp; Document knowledge</div>
          <div className="nav-item">♙ &nbsp; Employee services</div>
        </div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>Backend connection</strong>
            <p>Local development mode</p>
          </div>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">WORKSPACE / ASSISTANT</p>
            <h1>AI Employee Assistant</h1>
          </div>
          <div className="topbar-status">
            <span className="status-dot" /> API integration
          </div>
        </header>

        <section className="chat-area">
          <div className="welcome">
            <div className="welcome-icon">✳</div>
            <p className="eyebrow">YOUR WORKPLACE, SIMPLIFIED</p>
            <h2>How can I help you today?</h2>
            <p className="welcome-description">
              Get assistance with employee services and search your company
              documents from one place.
            </p>
          </div>

          <div className="suggestions">
            {suggestions.map((item) => (
              <button
                key={item}
                className="suggestion"
                onClick={() => setQuestion(item)}
              >
                ↗ &nbsp; {item}
              </button>
            ))}
          </div>

          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message ${message.role}`} key={index}>
                <div className="message-avatar">
                  {message.role === 'assistant' ? '✳' : 'Y'}
                </div>
                <div className="message-content">
                  <p className="message-author">
                    {message.role === 'assistant' ? 'AI Assistant' : 'You'}
                  </p>
                  <div className="message-text">{message.text}</div>

                  {message.agent && (
                    <div className="metadata">
                      <span>{message.agent}</span>
                      {message.tool && <span>Tool: {message.tool}</span>}
                    </div>
                  )}

                  {message.sources?.length > 0 && (
                    <details className="sources">
                      <summary>View retrieved sources</summary>
                      {message.sources.map((source, i) => (
                        <pre key={i}>
                          {typeof source === 'string'
                            ? source
                            : JSON.stringify(source, null, 2)}
                        </pre>
                      ))}
                    </details>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="loading-message">Assistant is working...</div>
            )}
          </div>

          <div className="composer-area">
            <form className="composer" onSubmit={sendMessage}>
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about HR, payroll, leave, or company documents..."
                rows={2}
                disabled={loading}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    event.currentTarget.form.requestSubmit()
                  }
                }}
              />
              <div className="composer-footer">
                <span>Enterprise knowledge assistant</span>
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                >
                  {loading ? 'Thinking...' : 'Send ↑'}
                </button>
              </div>
            </form>
            <p className="disclaimer">
              Responses depend on the backend and available documents.
            </p>
          </div>
        </section>
      </main>

      <aside className="right-panel">
        <div className="panel-heading">
          <p className="eyebrow">TOOLS & DATA</p>
          <h2>Workspace tools</h2>
          <p>Manage documents and employee queries.</p>
        </div>

        <section className="tool-card">
          <div className="tool-icon purple">▤</div>
          <h3>Knowledge documents</h3>
          <p>Upload a PDF to add it to document search.</p>
          <form onSubmit={uploadPDF}>
            <label className="file-picker">
              <span>＋</span>
              <span>{file ? file.name : 'Choose a PDF file'}</span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>
            <button className="upload-button" type="submit">
              Upload document
            </button>
          </form>
        </section>

        <section className="tool-card">
          <div className="tool-icon green">♙</div>
          <h3>Leave management</h3>
          <p>Prepare a leave-balance query for a demo employee.</p>
          <label className="field-label" htmlFor="employee-id">
            Employee ID
          </label>
          <input
            id="employee-id"
            className="text-input"
            value={employeeId}
            onChange={(event) => setEmployeeId(event.target.value)}
            placeholder="e.g. EMP001"
          />
          <button
            className="secondary-button"
            onClick={() =>
              setQuestion(`Check leave balance for ${employeeId}`)
            }
          >
            Prepare leave query
          </button>
        </section>

        <section className="info-card">
          <span className="info-icon">i</span>
          <div>
            <h3>Development environment</h3>
            <p>
              Connected to your local FastAPI server. Not yet deployed
              publicly.
            </p>
          </div>
        </section>

        <footer className="right-footer">
          Enterprise AI Employee Assistant
          <span>React + FastAPI + RAG</span>
        </footer>
      </aside>
    </div>
  )
}

export default App