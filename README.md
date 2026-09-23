# TriviaBlitz

A real-time multiplayer trivia game. Players join a lobby, answer 10 timed questions together, use power-ups, chat, and compete on a live leaderboard. The backend is Python with Socket.IO, and the frontend is React.

## Features

- **Real-time multiplayer:** a shared lobby with a 30-second matchmaking countdown, synchronized questions, live "player answered" indicators, and a reveal screen after every question.
- **Bots when you play alone:** if only one person joins, 1–3 bots fill the room. They answer after human-like delays (never under 2 seconds), and their accuracy drops as questions get harder.
- **Adaptive difficulty:** questions are rated 1–10. The next question gets harder after a correct answer and easier after a wrong one.
- **Speed-based scoring with streaks:** an instant answer is worth up to 1,000 points, falling to 100 at the 20-second limit. Consecutive correct answers add a multiplier of up to 2x.
- **Power-ups:**
  - **50/50** removes two wrong answers.
  - **Call a Friend** asks an LLM "friend" (GPT-4o-mini via PydanticAI) for a hint, delivered in a fun, slightly dramatic character.
  - **Double Score** doubles the points for one question.
- **Custom Topic mode:** type any topic, and GPT-4o-mini generates 10 questions about it on the spot.
- **Chat and emoji reactions** during the game.
- **Persistent stats:** SQLite stores every game's results, per-player statistics, and an all-time leaderboard.

## How the question bank was built

The questions in `data/` come from a four-step LLM pipeline in `scripts/` (`run_pipeline.py` runs all of it):

1. **Generate** (`generate_questions.py`): GPT-4o writes 300 questions, each with a difficulty rating, a correct answer, and three wrong answers.
2. **Deduplicate** (`verify_uniqueness.py`): GPT-4o reviews the set and removes repeats, leaving 294.
3. **Filter** (`filter_questions.py`): a smaller model, Gemini 2.5 Flash, answers every question with the options shuffled. Questions it gets wrong are dropped as too obscure or ambiguous, leaving 291.
4. **Build** (`build_database.py`): loads the final set into a SQLite database.

## Tech stack

- **Backend:** Python, python-socketio + aiohttp, aiosqlite, PydanticAI, OpenAI API
- **Frontend:** React 19, Vite, socket.io-client
- **Question pipeline:** OpenAI GPT-4o, Google Gemini 2.5 Flash, pandas

## Running locally

```bash
# 1. Python environment
python -m venv .venv
.venv\Scripts\activate          # Windows (on macOS/Linux: source .venv/bin/activate)
pip install -r backend/requirements.txt -r scripts/requirements.txt

# 2. API keys
cp .env.example .env           # then add your keys

# 3. Build the database from the included question set
python scripts/run_pipeline.py --only 4

# 4. Start the backend (http://localhost:8000)
python backend/server.py

# 5. Start the frontend, in a second terminal
cd frontend
npm install
npm run dev
```

On Windows, `start_server.ps1` and `start_frontend.ps1` do steps 4 and 5.

To play with friends on other devices, expose the backend with a tunnel such as ngrok or Pinggy, and point `BACKEND_URL` in `frontend/src/hooks/useSocket.js` at the public URL.
