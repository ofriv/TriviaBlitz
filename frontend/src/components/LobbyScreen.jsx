import { useState, useEffect } from 'react';
import Avatar from './Avatar';

const MAX_WAIT = 30;
const CIRCUMFERENCE = 2 * Math.PI * 44; // ≈ 276.46

export default function LobbyScreen({ players, countdown: serverCountdown, playerName, onSkipWait }) {
  const humanPlayers = players.filter(p => !p.is_bot);

  // Local countdown that ticks on its own — syncs to server value when it arrives
  const [countdown, setCountdown] = useState(serverCountdown ?? MAX_WAIT);

  useEffect(() => {
    if (serverCountdown != null) setCountdown(serverCountdown);
  }, [serverCountdown]);

  useEffect(() => {
    if (countdown <= 0) return;
    const id = setTimeout(() => setCountdown(t => Math.max(0, t - 1)), 1000);
    return () => clearTimeout(id);
  }, [countdown]);

  const progress = countdown / MAX_WAIT;
  const offset   = CIRCUMFERENCE * (1 - progress);

  return (
    <div className="screen">
      <div className="lobby">
        <h2>Waiting for Players</h2>
        <p className="sub">Game starts when the countdown reaches zero or enough players join</p>

        {/* Countdown ring */}
        <div className="countdown-wrap">
          <svg className="countdown-ring" viewBox="0 0 100 100">
            <defs>
              <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f5ead2" />
                <stop offset="100%" stopColor="#c9a878" />
              </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="44" className="track" />
            <circle
              cx="50" cy="50" r="44"
              className="fill"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={offset}
            />
          </svg>
          <div className="countdown-center">
            <span className="num">{countdown}</span>
            <span className="lbl">seconds</span>
          </div>
        </div>

        {/* Player list */}
        <div className="player-card card" style={{ width: '100%' }}>
          <div className="player-card-header">
            <span className="ttl">Players in lobby</span>
            <span className="count">{humanPlayers.length}</span>
          </div>
          <div className="player-list">
            {humanPlayers.map((p, i) => (
              <div key={p.name} className="player-row" style={{ animationDelay: `${i * 0.05}s` }}>
                <Avatar name={p.name} size={36} />
                <span className="name">
                  {p.name}
                  {p.name === playerName && <span className="you">YOU</span>}
                </span>
                <span className="status ready">Ready ✓</span>
              </div>
            ))}
            {humanPlayers.length === 0 && (
              <div className="player-slot-empty">
                <div className="pip">+</div>
                <span>Connecting…</span>
              </div>
            )}
          </div>
        </div>

        {/* Solo skip button */}
        {humanPlayers.length === 1 && (
          <div style={{ width: '100%', textAlign: 'center' }}>
            <button className="btn-primary" onClick={onSkipWait} style={{ width: '100%', justifyContent: 'center' }}>
              ⚡ Play Now
            </button>
            <p style={{ marginTop: 10, fontSize: 12, color: 'var(--text-3)' }}>
              Skip the wait — bots will fill the game
            </p>
          </div>
        )}

        {humanPlayers.length !== 1 && (
          <div className="hint">
            <strong>Solo?</strong> AI bots will fill the game so you're never alone!
          </div>
        )}
      </div>
    </div>
  );
}
