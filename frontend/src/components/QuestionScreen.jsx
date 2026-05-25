import { useState, useEffect, useRef } from 'react';
import Avatar from './Avatar';

const QUESTION_TIME    = 20;
const PREVIEW_DURATION = 2500; // ms the topic overlay stays up

export default function QuestionScreen({
  question,
  questionNum,
  players,
  myScore,
  powerups,
  friendHint,
  doubleActive,
  onAnswer,
  onPowerup,
}) {
  const [timeLeft, setTimeLeft]   = useState(QUESTION_TIME);
  const [selected, setSelected]   = useState(null);
  const [answered, setAnswered]   = useState(false);
  const [showHint, setShowHint]   = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  const startRef = useRef(Date.now());
  const qKey = question?.question_id ?? question?.question ?? '';

  // Reset everything (including preview) on new question
  useEffect(() => {
    setTimeLeft(QUESTION_TIME);
    setSelected(null);
    setAnswered(false);
    setShowHint(false);
    setShowPreview(true);
    startRef.current = Date.now();

    const id = setTimeout(() => setShowPreview(false), PREVIEW_DURATION);
    return () => clearTimeout(id);
  }, [qKey]);

  // Countdown timer — only runs while preview is dismissed and not answered
  useEffect(() => {
    if (answered || showPreview) return;
    const id = setInterval(() => {
      setTimeLeft(t => {
        if (t <= 1) { clearInterval(id); return 0; }
        return t - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [answered, showPreview, qKey]);

  useEffect(() => {
    if (friendHint) setShowHint(true);
  }, [friendHint]);

  const options = question?.options ?? [];
  const removed = question?._removed ?? [];

  const handleOptionClick = (opt) => {
    if (answered || removed.includes(opt) || showPreview) return;
    setSelected(opt);
    setAnswered(true);
    onAnswer(opt);
  };

  const handlePowerup = (type) => {
    if (!powerups[type] || answered || showPreview) return;
    onPowerup(type);
  };

  const progress   = (timeLeft / QUESTION_TIME) * 100;
  const timerState = timeLeft > 10 ? 'ok' : timeLeft > 5 ? 'warn' : 'danger';

  // difficulty comes from the DB as a number 1–10; map to easy/medium/hard
  const diffLabel = (() => {
    const d = question?.difficulty;
    if (d == null) return 'Medium';
    if (typeof d === 'string') return d; // already a label
    return d <= 3 ? 'Easy' : d <= 6 ? 'Medium' : 'Hard';
  })();
  const diffClass = `diff-${diffLabel.toLowerCase()}`;

  return (
    <>
      {/* ── Topic preview overlay ─────────────────────────────────────── */}
      {showPreview && question && (
        <div
          className="topic-preview"
          onClick={() => setShowPreview(false)}
          title="Click to skip"
        >
          <div className="topic-preview__card">
            <p className="topic-preview__sup">
              Question {questionNum} / 10 &nbsp;·&nbsp; Get Ready
            </p>
            <h2 className="topic-preview__cat">
              {question.category ?? 'General Knowledge'}
            </h2>
            <div className="topic-preview__badges">
              {question.difficulty && (
                <span className={`badge ${diffClass}`}>{diffLabel}</span>
              )}
            </div>
            {/* Draining progress bar — duration matches PREVIEW_DURATION */}
            <div className="topic-preview__bar-wrap">
              <div
                className="topic-preview__bar"
                style={{ animation: `drainProgress ${PREVIEW_DURATION}ms linear forwards` }}
              />
            </div>
            <p className="topic-preview__hint">Tap anywhere to skip</p>
          </div>
        </div>
      )}

      {/* ── Main question screen ───────────────────────────────────────── */}
      <div className="screen">
        <div className="question-screen">

          {/* Top bar */}
          <div className="q-topbar">
            <div className="q-num">
              <span className="cur">{questionNum}</span>
              <span className="tot">/ 10</span>
            </div>
            {question?.category && (
              <span className="badge cat">{question.category}</span>
            )}
            {question?.difficulty && (
              <span className={`badge ${diffClass}`}>{diffLabel}</span>
            )}
            {doubleActive && <span className="badge x2">×2 Score</span>}
            <div className="score-chip">
              <span className="coin" />
              {myScore.toLocaleString()}
            </div>
          </div>

          {/* Timer */}
          <div className="timer">
            <div className="timer-bar">
              <div
                className={`timer-fill ${showPreview ? 'ok' : timerState}`}
                style={{ width: showPreview ? '100%' : `${progress}%` }}
              />
            </div>
            <div className="timer-meta">
              <span>Time remaining</span>
              <span className={`timer-secs ${showPreview ? '' : timerState}`}>
                {showPreview ? `${QUESTION_TIME}s` : `${timeLeft}s`}
              </span>
            </div>
          </div>

          {/* Main layout */}
          <div className="q-layout">

            {/* Left column */}
            <div>
              <div className="question-card">
                <p className="q-text">{question?.question}</p>
              </div>

              <div className="answers">
                {options.map((opt, i) => {
                  const isRemoved  = removed.includes(opt);
                  const isSelected = selected === opt;
                  const isDimmed   = answered && !isSelected && !isRemoved;
                  return (
                    <button
                      key={i}
                      className={[
                        'answer',
                        isRemoved  ? 'removed'  : '',
                        isSelected ? 'selected' : '',
                        isDimmed   ? 'dimmed'   : '',
                      ].filter(Boolean).join(' ')}
                      onClick={() => handleOptionClick(opt)}
                      disabled={answered || isRemoved || showPreview}
                    >
                      <span className="letter">{['A', 'B', 'C', 'D'][i]}</span>
                      {opt}
                    </button>
                  );
                })}
              </div>

              <div className="powerups">
                <PowerupBtn
                  icon="✂️"
                  label="50 / 50"
                  sub="Remove two wrong answers"
                  active={powerups.fifty_fifty && !answered && !showPreview}
                  onClick={() => handlePowerup('fifty_fifty')}
                />
                <PowerupBtn
                  icon="📞"
                  label="Call Friend"
                  sub="Ask an AI friend for a hint"
                  active={powerups.call_friend && !answered && !showPreview}
                  onClick={() => handlePowerup('call_friend')}
                />
                <PowerupBtn
                  icon="×2"
                  label="Double Score"
                  sub="Double points for this answer"
                  active={powerups.double_score && !answered && !showPreview}
                  glow={doubleActive}
                  onClick={() => handlePowerup('double_score')}
                />
              </div>
            </div>

            {/* Right sidebar */}
            <div className="q-side">
              <div className="side-card">
                <div className="ttl">
                  <span>Players</span>
                  <span>{players.filter(p => p.answered).length}/{players.length}</span>
                </div>
                {players.map(p => (
                  <div key={p.name} className={`side-player ${p.answered ? 'answered' : ''}`}>
                    <Avatar name={p.name} size={28} />
                    <span className="nm">{p.name}</span>
                    {p.is_bot && <span className="bot">BOT</span>}
                    <div className="check">{p.answered ? '✓' : ''}</div>
                  </div>
                ))}
              </div>

              {showHint && friendHint && (
                <div className="cf-panel">
                  <div className="cf-head">📞 Friend says…</div>
                  <p className="cf-quote">"{friendHint}"</p>
                  <button
                    style={{ marginTop: 10, fontSize: 11, color: 'var(--text-3)', cursor: 'pointer' }}
                    onClick={() => setShowHint(false)}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>

          </div>
        </div>
      </div>
    </>
  );
}

function PowerupBtn({ icon, label, sub, active, glow, onClick }) {
  return (
    <button
      className={['pu', !active ? 'used' : '', glow ? 'active' : ''].filter(Boolean).join(' ')}
      onClick={onClick}
      disabled={!active}
    >
      <div className="pu-icon">{icon}</div>
      <div>
        <div className="pu-label">{label}</div>
        {sub && <div className="pu-sub">{sub}</div>}
      </div>
    </button>
  );
}
