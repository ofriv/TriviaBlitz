import { useState, useEffect } from 'react';
import Avatar from './Avatar';

const REVEAL_SECONDS = 3;

export default function RevealScreen({ revealData, playerName, questionNum, totalQuestions = 10 }) {
  const { correct_answer, results = [] } = revealData;

  const sorted = [...results].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
  const me     = results.find(r => r.name === playerName);

  // 3-2-1 countdown
  const [secondsLeft, setSecondsLeft] = useState(REVEAL_SECONDS);

  useEffect(() => {
    setSecondsLeft(REVEAL_SECONDS);
  }, [revealData]);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = setTimeout(() => setSecondsLeft(t => t - 1), 1000);
    return () => clearTimeout(id);
  }, [secondsLeft]);

  const rankClass = (i) => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';

  return (
    <div className="screen">
      <div className="reveal">

        {/* Correct answer banner */}
        <div className="correct-banner card">
          <div className="lbl">✅ Correct Answer</div>
          <div className="ans">{correct_answer}</div>
        </div>

        {/* My result + leaderboard grid */}
        <div className="reveal-grid">

          {/* My result */}
          {me ? (
            <div className={`result-card card ${me.correct ? 'correct' : 'wrong'}`}>
              <div className={`result-icon ${me.correct ? 'correct' : 'wrong'}`}>
                {me.correct ? '✓' : '✗'}
              </div>
              <div className="result-label">
                {me.correct ? 'Correct!' : 'Wrong answer'}
              </div>
              <div className={`result-points ${me.correct ? 'correct' : 'wrong'}`}>
                {me.correct
                  ? `+${(me.points_earned ?? 0).toLocaleString()}`
                  : '+0'}
              </div>
              {/* Streak info */}
              {me.correct && (me.streak_mult ?? 1) > 1 && (
                <div className="streak-bonus">
                  🔥 ×{me.streak_mult} streak bonus
                </div>
              )}
              {me.correct && (me.streak ?? 0) >= 2 && (
                <div className="streak-count">
                  {me.streak} in a row!
                </div>
              )}
              <div className="result-total">
                <span className="coin" />
                {(me.score ?? 0).toLocaleString()} pts total
              </div>
            </div>
          ) : (
            <div className="result-card card">
              <div className="result-label" style={{ marginTop: 24 }}>
                Question {questionNum} / {totalQuestions}
              </div>
            </div>
          )}

          {/* Leaderboard */}
          <div className="leaderboard card">
            <div style={{ padding: '12px 14px 4px', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '.1em' }}>
              Current Standings
            </div>
            {sorted.map((r, i) => (
              <div
                key={r.name}
                className={`lb-row ${r.name === playerName ? 'me' : ''} ${rankClass(i)}`}
              >
                <div className="rank">
                  {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                </div>
                <Avatar name={r.name} size={28} />
                <div className="nm">
                  {r.name}
                  {r.name === playerName && <span className="you">YOU</span>}
                </div>
                {r.correct && (
                  <span style={{ fontSize: 12, color: 'var(--green)', fontWeight: 700 }}>✓</span>
                )}
                <div className="pts">
                  <span className="coin" />
                  {(r.score ?? 0).toLocaleString()}
                </div>
              </div>
            ))}
          </div>

        </div>

        {/* 3-2-1 countdown to next question */}
        <div className="reveal-countdown">
          <div className={`reveal-countdown__num ${secondsLeft === 0 ? 'done' : ''}`}>
            {secondsLeft > 0 ? secondsLeft : '…'}
          </div>
          <div className="reveal-countdown__label">next question</div>
          <div className="reveal-countdown__dots">
            {[3, 2, 1].map(n => (
              <div
                key={n}
                className={`reveal-countdown__dot ${secondsLeft >= n ? 'active' : ''}`}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
