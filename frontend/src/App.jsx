import { useState, useEffect, useCallback } from 'react';
import { useSocket } from './hooks/useSocket';

import LandingScreen  from './components/LandingScreen';
import LobbyScreen    from './components/LobbyScreen';
import QuestionScreen from './components/QuestionScreen';
import RevealScreen   from './components/RevealScreen';
import GameOverScreen from './components/GameOverScreen';
import ChatPanel      from './components/ChatPanel';

/**
 * Screen states:
 *   landing → lobby → question → reveal → (loop) → gameover
 *
 * All Socket.IO event names match backend/server.py exactly.
 */
export default function App() {
  const socket = useSocket();

  const [screen, setScreen]         = useState('landing');
  const [playerName, setPlayerName] = useState('Alex');
  const [players, setPlayers]       = useState([]);          // [{name, is_bot, answered?, score?}]
  const [countdown, setCountdown]   = useState(30);
  const [question, setQuestion]     = useState(null);
  const [questionNum, setQNum]      = useState(0);
  const [totalQuestions, setTotalQ] = useState(10);
  const [revealData, setRevealData] = useState(null);
  const [gameResult, setGameResult] = useState(null);
  const [myScore, setMyScore]       = useState(0);
  const [myStreak, setMyStreak]     = useState(0);           // current correct streak
  const [chatMessages, setChatMessages] = useState([]);
  const [powerups, setPowerups]     = useState({
    fifty_fifty:  true,
    call_friend:  true,
    double_score: true,
  });
  const [friendHint, setFriendHint] = useState(null);
  const [doubleActive, setDoubleActive] = useState(false);

  // AI Custom Topic mode
  const [customTopic, setCustomTopic]   = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  // ── Socket event listeners ──────────────────────────────────────────────────
  useEffect(() => {
    // Initial lobby state (sent only to me after joining)
    socket.on('lobby_update', (data) => {
      setPlayers(data.players ?? []);
    });

    // Someone joined — update full player list
    socket.on('player_joined', (data) => {
      setPlayers(data.players ?? []);
    });

    // Someone left
    socket.on('player_left', (data) => {
      setPlayers(prev => prev.filter(p => p.name !== data.name));
    });

    // Matchmaking countdown tick — {seconds_remaining, players: [str, ...]}
    socket.on('lobby_countdown', (data) => {
      setCountdown(data.seconds_remaining ?? 30);
    });

    // AI question generation started — stay on lobby, show spinner
    socket.on('generating_questions', () => {
      setIsGenerating(true);
    });

    // AI questions ready (or fallback to DB) — spinner off
    socket.on('questions_ready', () => {
      setIsGenerating(false);
    });

    // Game is starting — {players: [{name, is_bot}], num_questions, custom_topic}
    // NOTE: do NOT call setScreen here — question is not yet available.
    // The 'question' event (arrives ~1s later) calls setScreen('question').
    socket.on('game_start', (data) => {
      console.log('[game_start] received', data);
      const gamePlayers = (data.players ?? []).map(p => ({
        ...p,
        score: 0,
        answered: false,
      }));
      setPlayers(gamePlayers);
      setMyScore(0);
      setMyStreak(0);
      setTotalQ(data.num_questions ?? 10);
      setPowerups({ fifty_fifty: true, call_friend: true, double_score: true });
      setChatMessages([]);
      setFriendHint(null);
      setDoubleActive(false);
      setIsGenerating(false);   // safety reset
      // Stay on lobby screen until the first 'question' event arrives
    });

    // New question — {question_number, question_id, question, options, difficulty, category, time_limit, total}
    socket.on('question', (data) => {
      console.log('[question] received', data);
      setQuestion(data);
      setQNum(data.question_number ?? 1);
      setTotalQ(data.total ?? 10);
      setRevealData(null);
      setFriendHint(null);
      setDoubleActive(false);
      setIsGenerating(false);  // safety reset
      setScreen('question');
    });

    // A player (human or bot) submitted an answer — mark them as answered
    socket.on('player_answered', (data) => {
      setPlayers(prev => prev.map(p =>
        p.name === data.player_name ? { ...p, answered: true } : p
      ));
    });

    // Correct answer revealed — {correct_answer, results: [{name, score, correct, points_earned, streak, streak_mult, is_bot}]}
    socket.on('answer_reveal', (data) => {
      setRevealData(data);
      if (data.results) {
        setPlayers(prev => prev.map(p => {
          const r = data.results.find(r => r.name === p.name);
          return r ? { ...p, score: r.score, answered: false } : { ...p, answered: false };
        }));
        const me = data.results.find(r => r.name === playerName);
        if (me) {
          setMyScore(me.score);
          setMyStreak(me.streak ?? 0);
        }
      }
      setScreen('reveal');
    });

    // Game finished — {leaderboard: [{name, score, is_bot, correct, wrong}], winner, game_id}
    socket.on('game_over', (data) => {
      setGameResult(data);
      setScreen('gameover');
    });

    // ── Power-up results ──────────────────────────────────────────────────────

    // 50/50 — {removed: [str, str], player_name}
    socket.on('fifty_fifty_result', (data) => {
      setQuestion(prev => prev ? { ...prev, _removed: data.removed } : prev);
    });

    // Double Score activated — {player_name}
    socket.on('double_score_activated', (data) => {
      if (data.player_name === playerName) {
        setDoubleActive(true);
      }
    });

    // Call-a-Friend response — {hint: str, player_name}
    socket.on('call_friend_result', (data) => {
      if (data.player_name === playerName) {
        setFriendHint(data.hint);
      }
    });

    // ── Chat ──────────────────────────────────────────────────────────────────
    socket.on('chat_message', (msg) => {
      setChatMessages(prev => [...prev.slice(-99), { type: 'text', ...msg }]);
    });

    socket.on('emoji_reaction', (data) => {
      setChatMessages(prev => [...prev.slice(-99), { type: 'emoji', ...data }]);
    });

    // ── Errors ────────────────────────────────────────────────────────────────
    socket.on('error', (data) => {
      console.warn('[Server error]', data.message);
    });

    return () => {
      socket.off('lobby_update');
      socket.off('player_joined');
      socket.off('player_left');
      socket.off('lobby_countdown');
      socket.off('generating_questions');
      socket.off('questions_ready');
      socket.off('game_start');
      socket.off('question');
      socket.off('player_answered');
      socket.off('answer_reveal');
      socket.off('game_over');
      socket.off('fifty_fifty_result');
      socket.off('double_score_activated');
      socket.off('call_friend_result');
      socket.off('chat_message');
      socket.off('emoji_reaction');
      socket.off('error');
    };
  }, [socket, playerName]);

  // ── Actions ─────────────────────────────────────────────────────────────────
  const joinLobby = useCallback((name, topic = '') => {
    setPlayerName(name);
    setCustomTopic(topic);
    setScreen('lobby');
    socket.emit('join_lobby', { player_name: name, custom_topic: topic });
  }, [socket]);

  const submitAnswer = useCallback((answer) => {
    socket.emit('submit_answer', { answer });
  }, [socket]);

  const usePowerup = useCallback((type) => {
    socket.emit('use_powerup', { type });
    setPowerups(prev => ({ ...prev, [type]: false }));
  }, [socket]);

  const sendChat = useCallback((message) => {
    socket.emit('chat_message', { message });
  }, [socket]);

  const sendEmoji = useCallback((emoji) => {
    socket.emit('send_emoji', { emoji });
  }, [socket]);

  const skipWait = useCallback(() => {
    socket.emit('skip_wait', {});
  }, [socket]);

  const goToMainMenu = useCallback(() => {
    setGameResult(null);
    setQuestion(null);
    setRevealData(null);
    setPlayers([]);
    setCountdown(30);
    setChatMessages([]);
    setMyStreak(0);
    setIsGenerating(false);
    setCustomTopic('');
    setTotalQ(10);
    setScreen('landing');
  }, []);

  // ── Render ───────────────────────────────────────────────────────────────────
  const showChat = ['lobby', 'question', 'reveal'].includes(screen);

  return (
    <div style={{ width: '100%', minHeight: '100vh', display: 'flex', position: 'relative' }}>
      {screen === 'landing' && (
        <LandingScreen onJoin={joinLobby} defaultName={playerName} />
      )}
      {screen === 'lobby' && (
        <LobbyScreen
          players={players}
          countdown={countdown}
          playerName={playerName}
          onSkipWait={skipWait}
          isGenerating={isGenerating}
          customTopic={customTopic}
        />
      )}
      {screen === 'question' && !question && (
        <div className="screen" style={{ alignItems: 'center', justifyContent: 'center' }}>
          <p style={{ color: 'var(--gold)', fontSize: '1.25rem', fontFamily: 'var(--font-display)', fontStyle: 'italic' }}>
            Starting game…
          </p>
        </div>
      )}
      {screen === 'question' && question && (
        <QuestionScreen
          question={question}
          questionNum={questionNum}
          totalQuestions={totalQuestions}
          players={players}
          myScore={myScore}
          myStreak={myStreak}
          powerups={powerups}
          friendHint={friendHint}
          doubleActive={doubleActive}
          onAnswer={submitAnswer}
          onPowerup={usePowerup}
        />
      )}
      {screen === 'reveal' && revealData && (
        <RevealScreen
          revealData={revealData}
          playerName={playerName}
          questionNum={questionNum}
          totalQuestions={totalQuestions}
        />
      )}
      {screen === 'gameover' && gameResult && (
        <GameOverScreen
          result={gameResult}
          playerName={playerName}
          totalQuestions={totalQuestions}
          onMainMenu={goToMainMenu}
        />
      )}
      {showChat && (
        <ChatPanel
          messages={chatMessages}
          playerName={playerName}
          onSend={sendChat}
          onEmoji={sendEmoji}
        />
      )}
    </div>
  );
}
