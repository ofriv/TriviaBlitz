"""
Main Socket.IO + aiohttp server for the Trivia game.

Events received from client:
  join_lobby      {name: str}
  submit_answer   {answer: str}
  use_powerup     {powerup: "fifty_fifty" | "call_friend" | "double_score"}
  chat_message    {message: str}
  send_emoji      {emoji: str}
  request_stats   {}
  request_leaderboard {}

Events emitted to client:
  lobby_countdown  {seconds_left, players}
  game_start       {players, num_questions, question_time}
  question         {index, total, id, question, options, difficulty, category, time_limit}
  player_answered  {player_name, is_bot, is_correct, points, scores}
  question_result  {correct_answer, scores, question_index}
  game_over        {leaderboard, winner}
  powerup_result   {powerup, data}   (e.g. fifty_fifty removed options)
  friend_advice    {advice: str}
  chat             {player_name, message, timestamp}
  emoji_reaction   {player_name, emoji, timestamp}
  player_joined    {name, players}
  player_left      {name, players}
  error            {message}
  your_stats       {stats}
  leaderboard      {entries}
"""

import os
import sys
import asyncio
import time
import io
import json

# Fix Windows UTF-8
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import socketio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from game import GameRoom
from database import get_player_stats, get_leaderboard
from call_friend import ask_friend

# ── Socket.IO setup ───────────────────────────────────────────────────────────
sio = socketio.AsyncServer(
    async_mode='aiohttp',
    cors_allowed_origins='*',   # allow React dev server
    logger=False,
    engineio_logger=False,
)
app = web.Application()
sio.attach(app)

# ── Game room registry ────────────────────────────────────────────────────────
# For simplicity: one shared lobby room. All connected players join the same game.
# Could be extended to multiple rooms later.
LOBBY_ROOM = "main_lobby"
current_game: GameRoom | None = None
lobby_lock = asyncio.Lock()

# sid → player_name
connected_players: dict[str, str] = {}


# ── Helper: emit wrapper ──────────────────────────────────────────────────────
async def emit_to_room(event: str, data: dict, room: str = None, to: str = None):
    if to:
        await sio.emit(event, data, to=to)
    elif room:
        await sio.emit(event, data, room=room)
    else:
        await sio.emit(event, data)


async def enter_room_fn(sid: str, room: str):
    await sio.enter_room(sid, room)


# ── Connection events ─────────────────────────────────────────────────────────
@sio.event
async def connect(sid, environ):
    print(f"[+] Client connected: {sid}")


@sio.event
async def disconnect(sid):
    global current_game
    name = connected_players.pop(sid, None)
    print(f"[-] Client disconnected: {sid} ({name})")

    if current_game and sid in current_game.human_players:
        current_game.remove_player(sid)
        remaining = [p.name for p in current_game.human_players.values()]

        await sio.emit("player_left", {
            "name": name,
            "players": remaining,
        }, room=LOBBY_ROOM)

        # If everyone left during waiting, cancel matchmaking
        if current_game.state == "waiting" or current_game.state == "countdown":
            if current_game.player_count == 0:
                current_game.cancel_matchmaking()
                current_game = None


# ── Lobby ─────────────────────────────────────────────────────────────────────
@sio.event
async def join_lobby(sid, data):
    global current_game

    name = data.get("name", "").strip()
    if not name:
        await sio.emit("error", {"message": "Name cannot be empty."}, to=sid)
        return

    # Limit name length
    name = name[:20]

    async with lobby_lock:
        # Create a new game room if none exists or previous game is finished
        if current_game is None or current_game.state == "finished":
            current_game = GameRoom(
                room_id=LOBBY_ROOM,
                emit_fn=emit_to_room,
                enter_room_fn=enter_room_fn,
            )

        if current_game.state not in ("waiting", "countdown"):
            await sio.emit("error", {"message": "A game is already in progress. Please wait."}, to=sid)
            return

        # Join the Socket.IO room
        await sio.enter_room(sid, LOBBY_ROOM)
        connected_players[sid] = name
        current_game.add_player(sid, name)

        players = [p.name for p in current_game.human_players.values()]
        await sio.emit("player_joined", {"name": name, "players": players}, room=LOBBY_ROOM)

        # Start matchmaking countdown when first player joins
        if current_game.player_count == 1:
            current_game.start_matchmaking_countdown()


# ── Answer submission ─────────────────────────────────────────────────────────
@sio.event
async def submit_answer(sid, data):
    if current_game is None or current_game.state != "in_game":
        return
    if sid not in current_game.human_players:
        return

    answer = data.get("answer", "")
    await current_game.handle_answer(sid, answer)


# ── Power-ups ─────────────────────────────────────────────────────────────────
@sio.event
async def use_powerup(sid, data):
    if current_game is None or current_game.state != "in_game":
        return
    if sid not in current_game.human_players:
        return

    powerup = data.get("powerup", "")
    player = current_game.human_players[sid]

    if powerup == "fifty_fifty":
        result = await current_game.handle_fifty_fifty(sid)
        if result:
            await sio.emit("powerup_result", {"powerup": "fifty_fifty", "data": result}, room=LOBBY_ROOM)
        else:
            await sio.emit("error", {"message": "Power-up already used or unavailable."}, to=sid)

    elif powerup == "double_score":
        ok = await current_game.handle_double_score(sid)
        if ok:
            await sio.emit("powerup_result", {
                "powerup": "double_score",
                "data": {"player_name": player.name}
            }, room=LOBBY_ROOM)
        else:
            await sio.emit("error", {"message": "Double score already used or unavailable."}, to=sid)

    elif powerup == "call_friend":
        if not player.use_powerup("call_friend"):
            await sio.emit("error", {"message": "Call a Friend already used."}, to=sid)
            return

        # Get the current question
        if current_game.current_question_index < 0:
            return
        question = current_game.questions[current_game.current_question_index]

        # Notify room that player is calling a friend
        await sio.emit("powerup_result", {
            "powerup": "call_friend",
            "data": {"player_name": player.name, "status": "calling"}
        }, room=LOBBY_ROOM)

        # Call friend async (don't block)
        asyncio.create_task(_call_friend_task(sid, player.name, question))

    else:
        await sio.emit("error", {"message": f"Unknown power-up: {powerup}"}, to=sid)


async def _call_friend_task(sid: str, player_name: str, question: dict):
    """Ask the LLM friend and emit the advice back."""
    advice = await ask_friend(question)
    await sio.emit("friend_advice", {
        "player_name": player_name,
        "advice": advice,
    }, room=LOBBY_ROOM)


# ── Chat ──────────────────────────────────────────────────────────────────────
@sio.event
async def chat_message(sid, data):
    name = connected_players.get(sid, "Unknown")
    message = str(data.get("message", "")).strip()[:200]  # limit length
    if not message:
        return
    ts = int(time.time() * 1000)
    await sio.emit("chat", {
        "player_name": name,
        "message": message,
        "timestamp": ts,
    }, room=LOBBY_ROOM)


@sio.event
async def send_emoji(sid, data):
    name = connected_players.get(sid, "Unknown")
    emoji = str(data.get("emoji", "")).strip()
    ALLOWED_EMOJIS = ["😂", "🔥", "👏", "😮", "🤔", "😅", "💯", "🎉", "😭", "🤯"]
    if emoji not in ALLOWED_EMOJIS:
        return
    ts = int(time.time() * 1000)
    await sio.emit("emoji_reaction", {
        "player_name": name,
        "emoji": emoji,
        "timestamp": ts,
    }, room=LOBBY_ROOM)


# ── Stats & Leaderboard ───────────────────────────────────────────────────────
@sio.event
async def request_stats(sid, data):
    name = connected_players.get(sid)
    if not name:
        return
    stats = await get_player_stats(name)
    await sio.emit("your_stats", {"stats": stats}, to=sid)


@sio.event
async def request_leaderboard(sid, data):
    entries = await get_leaderboard(limit=10)
    await sio.emit("leaderboard", {"entries": entries}, to=sid)


# ── HTTP health check ─────────────────────────────────────────────────────────
async def health(request):
    return web.Response(text="OK", content_type="text/plain")

app.router.add_get("/health", health)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🎮 Trivia server starting on http://localhost:{port}")
    web.run_app(app, host="0.0.0.0", port=port)
