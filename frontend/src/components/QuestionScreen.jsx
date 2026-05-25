import { useState, useEffect, useRef } from 'react';
import './QuestionScreen.css';

const QUESTION_TIME = 20; // seconds

export default function QuestionScreen({
  question,
  questionNum,
  players,
  myScore,
  powerups,
  friendHint,
  doubleActive,   // from App — server confirmed double_score_activated
  onAnswer,
  onPowerup,
}) {
  const [timeLeft, setTimeLeft]   = useState(QUESTION_TIME);
  const [selected, setSelected]   = useState(null);
  const [answered, setAnswered]   = useState(false);
  const [showHint, setShowHint]   = useState(false);
  const startRef = useRef(Date.now());
  // Use a unique key derived from question text to reset on new question
  const qKey = question?.question_id ?? question?.question ?? '';

  // Reset everything when question changes
  useEffect(() => {
    setTimeLeft(QUESTION_TIME);
    setSelected(null);
    setAnswered(false);
    setShowHint(false);
    startRef.current = Date.now();
  }, [qKey]);

  // Countdown timer
  useEffect(() => {
    if (answered) return;
    const id = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) { clearInterval(id); return 0; }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [answered, qKey]);

  // Show hint panel when friend hint arrives
  useEffect(() => {
    if (friendHint) setShowHint(true);
  }, [friendHint]);

  const options  = question?.options ?? [];
  const removed  = question?._removed ?? [];

  const handleOptionClick = (opt) => {
    if (answered || removed.includes(opt)) return;
    setSelected(opt);
    setAnswered(true);
    onAnswer(opt);
  };

  const handlePowerup = (type) => {
    if (!powerups[type] || answered) return;
    onPowerup(type);
  };

  const progress    = (timeLeft / QUESTION_TIME) * 100;
  const timerColor  = timeLeft > 10 ? 'var(--green)' : timeLeft > 5 ? 'var(--gold)' : 'var(--red)';

  return (
    <div className="qscreen fade-in">
      {/* Header */}
      <div className="qscreen__header">
        <div className="qscreen__meta">
          <span className="qscreen__qnum">Q{questionNum}/10</span>
          {question?.category && (
            <span className="qscreen__cat">{question.category}</span>
          )}
          {question?.difficulty && (
            <span className="qscreen__diff">Diff {question.difficulty}</span>
          )}
          {doubleActive && <span className="qscreen__x2">×2 SCORE</span>}
        </div>
        <div className="qscreen__score">💰 {myScore.toLocaleString()} pts</div>
      </div>

      {/* Timer bar */}
      <div className="qscreen__timer-wrap">
        <div
          className="qscreen__timer-bar"
          style={{
            width: `${progress}%`,
            background: timerColor,
            transition: 'width 1s linear, background .3s ease',
          }}
        />
        <span className="qscreen__timer-num" style={{ color: timerColor }}>{timeLeft}s</span>
      </div>

      {/* Question text */}
      <div className="qscreen__question card">
        <p className="qscreen__qtext">{question?.question}</p>
      </div>

      {/* Answer options */}
      <div className="qscreen__options">
        {options.map((opt, i) => {
          const isRemoved  = removed.includes(opt);
          const isSelected = selected === opt;
          return (
            <button
              key={i}
              className={[
                'qscreen__opt',
                isRemoved  ? 'qscreen__opt--removed'  : '',
                isSelected ? 'qscreen__opt--selected' : '',
                answered && !isSelected && !isRemoved ? 'qscreen__opt--dim' : '',
              ].join(' ').trim()}
              onClick={() => handleOptionClick(opt)}
              disabled={answered || isRemoved}
            >
              <span className="qscreen__opt-letter">{['A','B','C','D'][i]}</span>
              {opt}
            </button>
          );
        })}
      </div>

      {/* Call-a-Friend hint */}
      {showHint && friendHint && (
        <div className="qscreen__hint card fade-in">
          <div className="qscreen__hint-header">
            📞 <strong>Your friend says…</strong>
            <button className="qscreen__hint-close" onClick={() => setShowHint(false)}>✕</button>
          </div>
          <p>{friendHint}</p>
        </div>
      )}

      {/* Power-ups */}
      <div className="qscreen__powerups">
        <PowerupBtn
          icon="✂️"
          label="50/50"
          active={powerups.fifty_fifty && !answered}
          onClick={() => handlePowerup('fifty_fifty')}
          tooltip="Remove two wrong answers"
        />
        <PowerupBtn
          icon="📞"
          label="Call Friend"
          active={powerups.call_friend && !answered}
          onClick={() => handlePowerup('call_friend')}
          tooltip="Ask an AI friend for a hint"
        />
        <PowerupBtn
          icon="×2"
          label="Double Score"
          active={powerups.double_score && !answered}
          glow={doubleActive}
          onClick={() => handlePowerup('double_score')}
          tooltip="Double points for this answer"
        />
      </div>

      {/* Player sidebar */}
      <div className="qscreen__players">
        <p className="qscreen__players-title">Players</p>
        {players.map(p => (
          <div key={p.name} className={`qscreen__player ${p.answered ? 'qscreen__player--done' : ''}`}>
            <span className="qscreen__p-dot" style={{ background: p.is_bot ? 'var(--muted)' : 'var(--accent)' }} />
            <span className="qscreen__p-name">{p.name}</span>
            {p.answered && <span className="qscreen__p-check">✓</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

function PowerupBtn({ icon, label, active, glow, onClick, tooltip }) {
  return (
    <button
      className={[
        'powerup',
        !active ? 'powerup--used' : '',
        glow    ? 'powerup--glow' : '',
      ].join(' ').trim()}
      onClick={onClick}
      disabled={!active}
      title={tooltip}
    >
      <span className="powerup__icon">{icon}</span>
      <span className="powerup__label">{label}</span>
    </button>
  );
}
