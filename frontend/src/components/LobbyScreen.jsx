import './LobbyScreen.css';

export default function LobbyScreen({ players, countdown, playerName }) {
  const humanPlayers = players.filter(p => !p.is_bot);
  const progress = (countdown / 30) * 100;

  return (
    <div className="lobby fade-in">
      <div className="lobby__header">
        <h2 className="lobby__title">⏳ Waiting for Players</h2>
        <p className="lobby__sub">Game starts when the countdown reaches zero or enough players join</p>
      </div>

      {/* Countdown ring */}
      <div className="lobby__timer">
        <svg className="lobby__ring" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="44" className="lobby__ring-bg" />
          <circle
            cx="50" cy="50" r="44"
            className="lobby__ring-fill"
            style={{
              strokeDashoffset: `${276.46 * (1 - progress / 100)}`,
            }}
          />
        </svg>
        <span className="lobby__timer-num">{countdown}</span>
        <span className="lobby__timer-label">seconds</span>
      </div>

      {/* Player list */}
      <div className="lobby__players card">
        <h3 className="lobby__players-title">
          Players in lobby
          <span className="lobby__count">{humanPlayers.length}</span>
        </h3>
        <ul className="lobby__list">
          {humanPlayers.map((p, i) => (
            <li key={p.name} className="lobby__player" style={{ animationDelay: `${i * .05}s` }}>
              <span className="lobby__avatar">{p.name[0].toUpperCase()}</span>
              <span className="lobby__pname">
                {p.name}
                {p.name === playerName && <span className="lobby__you"> (you)</span>}
              </span>
              <span className="lobby__ready">✓</span>
            </li>
          ))}
          {humanPlayers.length === 0 && (
            <li className="lobby__empty">Connecting…</li>
          )}
        </ul>
      </div>

      <p className="lobby__hint">
        💡 Solo? AI bots will fill the game so you're never alone!
      </p>
    </div>
  );
}
