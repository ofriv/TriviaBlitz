import { StrictMode, Component } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] Caught error:', error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          background: '#2a0a16', color: '#e8d5a8', padding: 32, fontFamily: 'monospace'
        }}>
          <h2 style={{ marginBottom: 16 }}>Something went wrong</h2>
          <pre style={{ fontSize: 12, maxWidth: 640, whiteSpace: 'pre-wrap', color: '#ff8a8a' }}>
            {String(this.state.error)}
          </pre>
          <button
            style={{ marginTop: 24, padding: '10px 24px', background: '#c9a878', border: 'none', borderRadius: 8, cursor: 'pointer' }}
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
