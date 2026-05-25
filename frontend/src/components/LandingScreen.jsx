import { useState } from 'react';
import './LandingScreen.css';

export default function LandingScreen({ onJoin, defaultName }) {
  const [name, setName] = useState(defaultName || '');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) { setError('Please enter your name!'); return; }
    if (trimmed.length > 20) { setError('Name must be 20 chars or less'); return; }
    onJoin(trimmed);
  };

  return (
    <div className="landing fade-in">
      <div className="landing__hero">
        <div className="landing__trophy">🏆</div>
        <h1 className="landing__title">TriviaBlitz</h1>
        <p className="landing__subtitle">Real-time multiplayer trivia — outsmart the competition!</p>
      </div>

      <form className="landing__form card" onSubmit={handleSubmit}>
        <label className="landing__label">Your name</label>
        <input
          type="text"
          value={name}
          onChange={e => { setName(e.target.value); setError(''); }}
          placeholder="Enter your name…"
          maxLength={20}
          autoFocus
        />
        {error && <p className="landing__error">{error}</p>}
        <button type="submit" className="landing__btn">
          Join Game →
        </button>
      </form>

      <div className="landing__features">
        <span>⚡ 10 Questions</span>
        <span>🎯 Adaptive Difficulty</span>
        <span>⏱ 20s Timer</span>
        <span>🤖 AI Bots</span>
      </div>
    </div>
  );
}
