import { useState } from 'react';

export default function LandingScreen({ onJoin, defaultName }) {
  const [name, setName]   = useState(defaultName || '');
  const [error, setError] = useState('');
  const [mode, setMode]   = useState('standard');  // 'standard' | 'ai'
  const [topic, setTopic] = useState('');

  const handleJoin = () => {
    const trimmed = name.trim();
    if (!trimmed)            { setError('Please enter a name'); return; }
    if (trimmed.length > 20) { setError('Name must be 20 characters or less'); return; }
    if (mode === 'ai' && !topic.trim()) {
      setError('Please enter a topic for AI questions');
      return;
    }
    onJoin(trimmed, mode === 'ai' ? topic.trim() : '');
  };

  return (
    <div className="screen">
      <div className="landing">
        <div className="eyebrow">Round starts in 30s</div>

        <h1>Trivia<span className="accent">Blitz</span></h1>

        <p className="tagline">
          Fast-paced trivia with friends, strangers, and surprisingly smart bots.
        </p>

        {/* ── Mode toggle ──────────────────────────────────────────────── */}
        <div className="mode-toggle">
          <button
            className={`mode-btn ${mode === 'standard' ? 'active' : ''}`}
            onClick={() => { setMode('standard'); setError(''); }}
          >
            📚 Standard
          </button>
          <button
            className={`mode-btn ${mode === 'ai' ? 'active' : ''}`}
            onClick={() => { setMode('ai'); setError(''); }}
          >
            🤖 AI Custom
          </button>
        </div>

        {/* ── AI topic input ────────────────────────────────────────────── */}
        {mode === 'ai' && (
          <div className="topic-wrap">
            <input
              type="text"
              className="topic-input"
              placeholder='e.g. "1990s anime", "graph algorithms", "Roman history"'
              value={topic}
              onChange={e => { setTopic(e.target.value); setError(''); }}
              onKeyDown={e => e.key === 'Enter' && handleJoin()}
              maxLength={80}
            />
            <p className="topic-hint">
              Claude will generate 10 fresh trivia questions on any topic you choose.
            </p>
          </div>
        )}

        {/* ── Name + join ───────────────────────────────────────────────── */}
        <div className="join">
          <input
            type="text"
            placeholder="Pick a name…"
            value={name}
            onChange={e => { setName(e.target.value); setError(''); }}
            onKeyDown={e => e.key === 'Enter' && handleJoin()}
            maxLength={20}
          />
          <button className="btn-primary" onClick={handleJoin}>
            {mode === 'ai' ? 'Generate & Play →' : 'Join Game →'}
          </button>
        </div>
        {error && <p className="error">{error}</p>}

        <div className="feature-row">
          <div className="feature-pill"><span className="ico">⚡</span>Real-time multiplayer</div>
          <div className="feature-pill"><span className="ico">🤖</span>AI bots fill empty slots</div>
          <div className="feature-pill"><span className="ico">🔥</span>Streak multipliers</div>
          <div className="feature-pill"><span className="ico">✨</span>AI custom questions</div>
        </div>

        <div className="stats">
          <div className="stat"><div className="n">2,847</div><div className="l">Playing now</div></div>
          <div className="stat"><div className="n">14k</div><div className="l">Questions</div></div>
          <div className="stat"><div className="n">87</div><div className="l">Categories</div></div>
        </div>
      </div>
    </div>
  );
}
