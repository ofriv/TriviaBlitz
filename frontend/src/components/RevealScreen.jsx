import './RevealScreen.css';

export default function RevealScreen({ revealData, playerName, questionNum }) {
  const { correct_answer, results = [], scores = {} } = revealData;

  // Sort by score descending
  const sorted = [...results].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  const me = results.find(r => r.name === playerName);
  const myResult = me;

  return (
    <div className="reveal fade-in">
      <div className="reveal__header">
        <span className="reveal__qnum">Question {questionNum} / 10</span>
        <h2 className="reveal__title">Answer Revealed!</h2>
      </div>

      {/* Correct answer */}
      <div className="reveal__correct card">
        <span className="reveal__correct-label">✅ Correct answer</span>
        <p className="reveal__correct-text">{correct_answer}</p>
      </div>

      {/* My result */}
      {myResult && (
        <div className={`reveal__my-result card ${myResult.correct ? 'reveal__my-result--correct' : 'reveal__my-result--wrong'}`}>
          {myResult.correct ? (
            <>
              <span className="reveal__icon">🎉</span>
              <span>You got it! <strong>+{myResult.points_earned?.toLocaleString() ?? '?'} pts</strong></span>
            </>
          ) : (
            <>
              <span className="reveal__icon">❌</span>
              <span>Not this time! Total: <strong>{myResult.score?.toLocaleString() ?? '?'} pts</strong></span>
            </>
          )}
        </div>
      )}

      {/* Scoreboard */}
      <div className="reveal__scores card">
        <h3 className="reveal__scores-title">Current Standings</h3>
        <ol className="reveal__list">
          {sorted.map((r, i) => (
            <li key={r.name} className={`reveal__entry ${r.name === playerName ? 'reveal__entry--me' : ''}`}>
              <span className="reveal__rank">
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}
              </span>
              <span className="reveal__pname">{r.name}</span>
              {r.correct && <span className="reveal__correct-badge">✓</span>}
              <span className="reveal__pscore">{(r.score ?? 0).toLocaleString()}</span>
            </li>
          ))}
        </ol>
      </div>

      <p className="reveal__next">Next question in a moment…</p>
    </div>
  );
}
