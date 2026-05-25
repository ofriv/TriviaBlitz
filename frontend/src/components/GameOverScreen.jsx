import Avatar from './Avatar';

const CONFETTI_COLORS = [
  '#e8d5a8', '#c9a878', '#8fb87a', '#e08585',
  '#b8a890', '#f5ead2', '#5a2640', '#d4a017',
];

function Confetti() {
  const pieces = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    width: `${6 + Math.random() * 8}px`,
    height: `${10 + Math.random() * 12}px`,
    color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
    delay: `${Math.random() * 3}s`,
    duration: `${2.5 + Math.random() * 2}s`,
  }));

  return (
    <div className="confetti">
      {pieces.map(p => (
        <i
          key={p.id}
          style={{
            left: p.left,
            width: p.width,
            height: p.height,
            background: p.color,
            animationDelay: p.delay,
            animationDuration: p.duration,
          }}
        />
      ))}
    </div>
  );
}

export default function GameOverScreen({ result, playerName, totalQuestions = 10, onMainMenu }) {
  const { leaderboard = [], game_id } = result;
  const myEntry = leaderboard.find(e => e.name === playerName);
  const myRank  = leaderboard.findIndex(e => e.name === playerName) + 1;
  const winner  = leaderboard[0];

  const rankEmoji = myRank === 1 ? '🥇' : myRank === 2 ? '🥈' : myRank === 3 ? '🥉' : `#${myRank}`;
  const congrats  = myRank === 1 ? 'Flawless victory!'
                  : myRank === 2 ? 'Runner-up — so close!'
                  : myRank === 3 ? 'Third place — solid run!'
                  : 'Good game — keep practicing!';

  const rankClass = (i) => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';

  return (
    <div className="screen">
      <div className="gameover">

        {myRank <= 3 && <Confetti />}

        {/* Hero section */}
        <div className="go-hero">
          <div className="eyebrow">🏆 Game Over</div>
          <h2>
            {myRank === 1 ? <>You <span className="accent">Won!</span></> : <><span className="accent">Final</span> Results</>}
          </h2>
          {winner && (
            <div className="winner-name">
              <span className="crown">👑</span>
              {winner.name} wins with {(winner.score ?? 0).toLocaleString()} pts
            </div>
          )}
        </div>

        {/* My stats */}
        {myEntry && (
          <div className="go-stats">
            <div className="go-stat card">
              <div className="v gold">{rankEmoji}</div>
              <div className="l">Your Rank</div>
            </div>
            <div className="go-stat card">
              <div className="v gold">{(myEntry.score ?? 0).toLocaleString()}</div>
              <div className="l">Points</div>
            </div>
            <div className="go-stat card">
              <div className="v green">{myEntry.correct ?? 0}</div>
              <div className="l">Correct</div>
            </div>
            <div className="go-stat card">
              <div className="v red">{myEntry.wrong ?? 0}</div>
              <div className="l">Wrong</div>
            </div>
          </div>
        )}

        {/* Leaderboard */}
        <div className="leaderboard card">
          <div style={{ padding: '14px 16px 4px', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '.1em' }}>
            Final Leaderboard
          </div>
          {leaderboard.map((entry, i) => (
            <div
              key={entry.name}
              className={`lb-row ${entry.name === playerName ? 'me' : ''} ${rankClass(i)}`}
            >
              <div className="rank">
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
              </div>
              <Avatar name={entry.name} size={28} />
              <div className="nm">
                {entry.name}
                {entry.name === playerName && <span className="you">YOU</span>}
                {entry.is_bot && (
                  <span style={{ fontSize: 9, color: 'var(--text-3)', background: 'var(--bg-2)', padding: '2px 5px', borderRadius: 4, fontWeight: 700, letterSpacing: '.05em' }}>BOT</span>
                )}
              </div>
              <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 600 }}>
                {entry.correct ?? 0}/{totalQuestions}
              </span>
              <div className="pts">
                <span className="coin" />
                {(entry.score ?? 0).toLocaleString()}
              </div>
            </div>
          ))}
        </div>

        <div className="go-actions">
          <button className="btn-primary" onClick={onMainMenu}>
            🏠 Main Menu
          </button>
        </div>

        {game_id && (
          <p style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: 'var(--text-3)' }}>
            Game #{game_id}
          </p>
        )}
      </div>
    </div>
  );
}
