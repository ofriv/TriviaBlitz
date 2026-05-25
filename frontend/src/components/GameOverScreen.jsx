import './GameOverScreen.css';

export default function GameOverScreen({ result, playerName, onPlayAgain }) {
  const { leaderboard = [], game_id } = result;
  const myEntry = leaderboard.find(e => e.name === playerName);
  const myRank  = leaderboard.findIndex(e => e.name === playerName) + 1;

  const rankEmoji = myRank === 1 ? '🥇' : myRank === 2 ? '🥈' : myRank === 3 ? '🥉' : `#${myRank}`;
  const congrats  = myRank === 1 ? "You won! Outstanding performance! 🎉"
                  : myRank === 2 ? "Runner-up! So close! 🌟"
                  : myRank === 3 ? "Third place! Solid effort! 👏"
                  : "Good game! Practice makes perfect! 💪";

  return (
    <div className="gameover fade-in">
      <div className="gameover__fireworks">
        {myRank <= 3 && ['🎆','🎇','✨','🎊'].map((e, i) => (
          <span key={i} className="gameover__spark" style={{ animationDelay: `${i * .2}s` }}>{e}</span>
        ))}
      </div>

      <h1 className="gameover__title">Game Over!</h1>
      <p className="gameover__congrats">{congrats}</p>

      {/* My result card */}
      {myEntry && (
        <div className="gameover__me card">
          <span className="gameover__my-rank">{rankEmoji}</span>
          <div>
            <p className="gameover__my-name">{playerName}</p>
            <p className="gameover__my-score">{(myEntry.score ?? 0).toLocaleString()} pts</p>
          </div>
          <div className="gameover__my-stats">
            <span>✅ {myEntry.correct ?? 0} correct</span>
            <span>❌ {myEntry.wrong ?? 0} wrong</span>
          </div>
        </div>
      )}

      {/* Full leaderboard */}
      <div className="gameover__board card">
        <h2 className="gameover__board-title">🏆 Final Leaderboard</h2>
        <ol className="gameover__list">
          {leaderboard.map((entry, i) => (
            <li
              key={entry.name}
              className={`gameover__entry ${entry.name === playerName ? 'gameover__entry--me' : ''}`}
            >
              <span className="gameover__pos">
                {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}`}
              </span>
              <span className="gameover__ename">
                {entry.name}
                {entry.is_bot && <span className="gameover__bot"> 🤖</span>}
              </span>
              <span className="gameover__correct">{entry.correct ?? 0}/10</span>
              <span className="gameover__escore">{(entry.score ?? 0).toLocaleString()}</span>
            </li>
          ))}
        </ol>
      </div>

      <button className="gameover__play-again" onClick={onPlayAgain}>
        🔄 Play Again
      </button>

      {game_id && (
        <p className="gameover__id">Game #{game_id}</p>
      )}
    </div>
  );
}
