"""
Game state management.

Handles:
  - Matchmaking lobby (30s wait)
  - Running a 10-question game
  - Adaptive difficulty (correct→harder, wrong→easier, clamped 1-10)
  - Time-decay scoring (max 1000 → ~100 over 20s)
  - Power-up logic (50/50, call_friend, double_score)
  - Bot answer scheduling
  - Saving results to DB
"""

import asyncio
import random
import time
from typing import Callable, Awaitable

from bot import BotPlayer, create_bots, calculate_bot_count
from database import fetch_question_by_difficulty_range, save_game_result

# ── Scoring constants ──────────────────────────────────────────────────────────
QUESTION_TIME_LIMIT = 20       # seconds per question
MAX_POINTS = 1000
MIN_POINTS = 100
# Points decay linearly from MAX_POINTS at t=0 to MIN_POINTS at t=QUESTION_TIME_LIMIT

# ── Game constants ─────────────────────────────────────────────────────────────
QUESTIONS_PER_GAME = 10
MATCHMAKING_WAIT = 30          # seconds
QUESTION_REVEAL_DELAY = 3      # seconds between leaderboard and next question


def calculate_score(time_taken_ms: int, double_score: bool = False) -> int:
    """
    Time-decay scoring:
      - Answer instantly (0ms)  → 1000 pts
      - Answer at 20s           → 100 pts
      - Linear interpolation in between
    """
    seconds = time_taken_ms / 1000.0
    seconds = max(0, min(seconds, QUESTION_TIME_LIMIT))
    fraction_remaining = 1.0 - (seconds / QUESTION_TIME_LIMIT)
    points = int(MIN_POINTS + (MAX_POINTS - MIN_POINTS) * fraction_remaining)
    if double_score:
        points *= 2
    return points


def adapt_difficulty(current_difficulty: int, was_correct: bool) -> int:
    """
    Adaptive difficulty:
      correct → increase difficulty by 1 (max 10)
      wrong   → decrease difficulty by 1 (min 1)
    """
    if was_correct:
        return min(10, current_difficulty + 1)
    else:
        return max(1, current_difficulty - 1)


class PlayerState:
    """Tracks in-game state for a single human player."""

    def __init__(self, sid: str, name: str):
        self.sid = sid
        self.name = name
        self.score = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self.current_difficulty = 5        # start at medium difficulty
        self.powerups = {
            "fifty_fifty": True,
            "call_friend": True,
            "double_score": True,
        }
        self.answered_this_question = False
        self.double_score_active = False   # activated for current question
        self.answers_log = []              # list of answer dicts for DB

    def use_powerup(self, powerup: str) -> bool:
        """Mark a power-up as used. Returns False if already used."""
        if self.powerups.get(powerup):
            self.powerups[powerup] = False
            return True
        return False

    def record_answer(self, question_id: int, question_order: int,
                      answer_given: str | None, is_correct: bool,
                      time_taken_ms: int, points_earned: int, powerup_used: str | None):
        self.answers_log.append({
            "player_name": self.name,
            "question_id": question_id,
            "question_order": question_order,
            "answer_given": answer_given,
            "is_correct": is_correct,
            "time_taken_ms": time_taken_ms,
            "points_earned": points_earned,
            "powerup_used": powerup_used,
        })
        if is_correct:
            self.correct_answers += 1
        else:
            self.wrong_answers += 1
        self.score += points_earned
        self.current_difficulty = adapt_difficulty(self.current_difficulty, is_correct)


class GameRoom:
    """
    Manages one full game session from matchmaking → finish.

    The `emit` callable sends Socket.IO events to players.
    Signature: emit(event, data, room=None, to=None)
    """

    def __init__(self, room_id: str, emit_fn: Callable, enter_room_fn: Callable):
        self.room_id = room_id
        self.emit = emit_fn           # async emit function
        self.enter_room = enter_room_fn

        # Players
        self.human_players: dict[str, PlayerState] = {}  # sid → PlayerState
        self.bot_players: list[BotPlayer] = []

        # Game state
        self.state = "waiting"        # waiting | countdown | in_game | finished
        self.questions: list[dict] = []
        self.current_question_index = -1
        self.current_question_start: float = 0
        self.used_question_ids: list[int] = []

        # Per-question answer tracking: name → {correct: bool, points: int}
        self.answers_received: dict[str, dict] = {}

        # Tasks
        self._question_timer_task: asyncio.Task | None = None
        self._matchmaking_task: asyncio.Task | None = None

    # ── Lobby ─────────────────────────────────────────────────────────────────

    def add_player(self, sid: str, name: str):
        self.human_players[sid] = PlayerState(sid, name)

    def remove_player(self, sid: str):
        self.human_players.pop(sid, None)

    @property
    def player_count(self):
        return len(self.human_players)

    def start_matchmaking_countdown(self):
        """Start the 30s matchmaking timer (called when first player joins)."""
        if self._matchmaking_task is None or self._matchmaking_task.done():
            self._matchmaking_task = asyncio.create_task(self._matchmaking_loop())

    async def _matchmaking_loop(self):
        """Wait up to 30s, then start the game."""
        self.state = "countdown"
        try:
            for remaining in range(MATCHMAKING_WAIT, 0, -1):
                print(f"[Lobby] countdown {remaining}", flush=True)
                await self.emit("lobby_countdown", {
                    "seconds_remaining": remaining,
                    "players": [p.name for p in self.human_players.values()]
                }, room=self.room_id)
                await asyncio.sleep(1)
            await self._start_game()
        except asyncio.CancelledError:
            print("[Lobby] matchmaking cancelled", flush=True)
            raise
        except Exception as e:
            print(f"[Lobby] matchmaking error: {e}", flush=True)
            raise

    def cancel_matchmaking(self):
        if self._matchmaking_task and not self._matchmaking_task.done():
            self._matchmaking_task.cancel()

    # ── Game start ────────────────────────────────────────────────────────────

    async def force_start(self):
        """Cancel the matchmaking wait and start the game immediately (solo skip)."""
        if self.state not in ("waiting", "countdown"):
            return
        self.cancel_matchmaking()
        # Yield one event-loop tick so CancelledError is delivered to the
        # matchmaking task before _start_game runs (avoids any double-start).
        await asyncio.sleep(0)
        await self._start_game()

    async def _start_game(self):
        """Begin the game: add bots if needed, load first question."""
        if self.player_count == 0 or self.state == "in_game":
            return

        # Add bots if solo player
        num_bots = calculate_bot_count(self.player_count)
        self.bot_players = create_bots(num_bots)

        self.state = "in_game"

        # Send players as objects so frontend knows who is a bot
        all_players = (
            [{"name": p.name, "is_bot": False} for p in self.human_players.values()]
            + [{"name": b.name, "is_bot": True} for b in self.bot_players]
        )

        await self.emit("game_start", {
            "players": all_players,
            "num_questions": QUESTIONS_PER_GAME,
            "question_time": QUESTION_TIME_LIMIT,
        }, room=self.room_id)

        await asyncio.sleep(1)
        await self._next_question()

    # ── Questions ─────────────────────────────────────────────────────────────

    async def _next_question(self):
        """Load and send the next question."""
        self.current_question_index += 1

        if self.current_question_index >= QUESTIONS_PER_GAME:
            await self._end_game()
            return

        # Determine target difficulty based on average human difficulty
        if self.human_players:
            avg_diff = sum(p.current_difficulty for p in self.human_players.values()) / len(self.human_players)
            target = round(avg_diff)
        else:
            target = 5

        # Fetch a question within ±1 of target difficulty
        question = await fetch_question_by_difficulty_range(
            max(1, target - 1), min(10, target + 1),
            exclude_ids=self.used_question_ids
        )
        # Fallback: any difficulty
        if not question:
            question = await fetch_question_by_difficulty_range(1, 10, self.used_question_ids)
        if not question:
            await self._end_game()
            return

        self.used_question_ids.append(question["id"])
        self.questions.append(question)

        # Reset per-question state
        self.answers_received = {}
        for player in self.human_players.values():
            player.answered_this_question = False
            player.double_score_active = False

        # Shuffle answer options before sending
        options = self._shuffle_options(question)

        self.current_question_start = time.time()

        await self.emit("question", {
            "question_number": self.current_question_index + 1,  # 1-indexed for display
            "question_id": question["id"],
            "index": self.current_question_index,
            "total": QUESTIONS_PER_GAME,
            "question": question["question"],
            "options": options,          # shuffled list of 4 strings
            "difficulty": question["difficulty"],
            "category": question["category"],
            "time_limit": QUESTION_TIME_LIMIT,
        }, room=self.room_id)

        # Schedule bot answers
        for bot in self.bot_players:
            asyncio.create_task(self._schedule_bot_answer(bot, question))

        # Schedule question timeout
        if self._question_timer_task and not self._question_timer_task.done():
            self._question_timer_task.cancel()
        self._question_timer_task = asyncio.create_task(
            self._question_timeout(question)
        )

    def _shuffle_options(self, question: dict) -> list[str]:
        """Return the 4 options in random order."""
        options = [question["correct"], question["wrong1"],
                   question["wrong2"], question["wrong3"]]
        random.shuffle(options)
        return options

    async def _schedule_bot_answer(self, bot: BotPlayer, question: dict):
        """Bot thinks, then submits its answer."""
        answer_text, delay = bot.decide_answer(question)
        await asyncio.sleep(delay)
        if self.state != "in_game":
            return
        # Check we're still on the same question
        q_idx = self.questions.index(question) if question in self.questions else -1
        if q_idx != self.current_question_index:
            return

        is_correct = (answer_text == question["correct"])
        time_taken_ms = int(delay * 1000)
        points = calculate_score(time_taken_ms) if is_correct else 0
        bot.add_score(points, is_correct)

        self.answers_received[bot.name] = {"correct": is_correct, "points": points}

        await self.emit("player_answered", {
            "player_name": bot.name,
            "is_bot": True,
        }, room=self.room_id)

        await self._check_all_answered(question)

    async def _question_timeout(self, question: dict):
        """Called after QUESTION_TIME_LIMIT seconds — move to next question."""
        await asyncio.sleep(QUESTION_TIME_LIMIT)
        if self.state != "in_game":
            return
        # Record timeout (no answer) for humans who haven't answered
        for player in self.human_players.values():
            if not player.answered_this_question:
                player.record_answer(
                    question_id=question["id"],
                    question_order=self.current_question_index + 1,
                    answer_given=None,
                    is_correct=False,
                    time_taken_ms=QUESTION_TIME_LIMIT * 1000,
                    points_earned=0,
                    powerup_used=None,
                )
                player.answered_this_question = True

        await self._reveal_answer(question)

    async def _check_all_answered(self, question: dict):
        """If everyone has answered, reveal immediately."""
        all_human_answered = all(p.answered_this_question for p in self.human_players.values())
        all_bot_answered = all(b.name in self.answers_received for b in self.bot_players)

        if all_human_answered and all_bot_answered:
            if self._question_timer_task and not self._question_timer_task.done():
                self._question_timer_task.cancel()
            await self._reveal_answer(question)

    async def _reveal_answer(self, question: dict):
        """Send the correct answer and per-question results."""
        # Build per-player result rows
        results = []
        for p in self.human_players.values():
            info = self.answers_received.get(p.name, {})
            results.append({
                "name": p.name,
                "score": p.score,
                "correct": info.get("correct", False),
                "points_earned": info.get("points", 0),
                "is_bot": False,
            })
        for b in self.bot_players:
            info = self.answers_received.get(b.name, {})
            results.append({
                "name": b.name,
                "score": b.score,
                "correct": info.get("correct", False),
                "points_earned": info.get("points", 0),
                "is_bot": True,
            })

        await self.emit("answer_reveal", {
            "correct_answer": question["correct"],
            "results": results,
            "question_index": self.current_question_index,
        }, room=self.room_id)

        await asyncio.sleep(QUESTION_REVEAL_DELAY)
        await self._next_question()

    # ── Answer handling ───────────────────────────────────────────────────────

    async def handle_answer(self, sid: str, answer: str, powerup_used: str | None = None):
        """
        Called when a human player submits an answer.
        """
        player = self.human_players.get(sid)
        if not player or player.answered_this_question:
            return

        player.answered_this_question = True
        question = self.questions[self.current_question_index]
        elapsed_ms = int((time.time() - self.current_question_start) * 1000)
        elapsed_ms = min(elapsed_ms, QUESTION_TIME_LIMIT * 1000)

        is_correct = (answer == question["correct"])
        double = player.double_score_active
        points = calculate_score(elapsed_ms, double_score=double) if is_correct else 0

        actual_powerup = "double_score" if double else powerup_used

        player.record_answer(
            question_id=question["id"],
            question_order=self.current_question_index + 1,
            answer_given=answer,
            is_correct=is_correct,
            time_taken_ms=elapsed_ms,
            points_earned=points,
            powerup_used=actual_powerup,
        )

        # Track for reveal
        self.answers_received[player.name] = {"correct": is_correct, "points": points}

        await self.emit("player_answered", {
            "player_name": player.name,
            "is_bot": False,
        }, room=self.room_id)

        await self._check_all_answered(question)

    # ── Power-ups ─────────────────────────────────────────────────────────────

    async def handle_fifty_fifty(self, sid: str) -> dict | None:
        """Remove 2 wrong answers. Returns {removed: [str, str]} or None if already used."""
        player = self.human_players.get(sid)
        if not player or not player.use_powerup("fifty_fifty"):
            return None
        question = self.questions[self.current_question_index]
        wrongs = [question["wrong1"], question["wrong2"], question["wrong3"]]
        removed = random.sample(wrongs, 2)
        return {"removed": removed, "player_name": player.name}

    async def handle_double_score(self, sid: str) -> bool:
        """Activate double score for this question. Returns True if successful."""
        player = self.human_players.get(sid)
        if not player or not player.use_powerup("double_score"):
            return False
        player.double_score_active = True
        return True

    # ── Scores ────────────────────────────────────────────────────────────────

    def _get_scores(self) -> list[dict]:
        """Return sorted leaderboard snapshot with full stats."""
        scores = []
        for p in self.human_players.values():
            scores.append({
                "name": p.name,
                "score": p.score,
                "is_bot": False,
                "correct": p.correct_answers,
                "wrong": p.wrong_answers,
            })
        for b in self.bot_players:
            scores.append({
                "name": b.name,
                "score": b.score,
                "is_bot": True,
                "correct": b.correct_answers,
                "wrong": b.wrong_answers,
            })
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores

    # ── End game ──────────────────────────────────────────────────────────────

    async def _end_game(self):
        """Finalize scores, send results, save to DB."""
        self.state = "finished"

        scores = self._get_scores()
        winner = scores[0] if scores else None

        # Build DB payload
        players_data = []
        all_answers = []
        for rank, entry in enumerate(scores, start=1):
            if not entry["is_bot"]:
                p = next(p for p in self.human_players.values() if p.name == entry["name"])
                players_data.append({
                    "player_name": p.name,
                    "is_bot": False,
                    "final_score": p.score,
                    "correct_answers": p.correct_answers,
                    "wrong_answers": p.wrong_answers,
                    "rank": rank,
                })
                all_answers.extend(p.answers_log)
            else:
                b = next(b for b in self.bot_players if b.name == entry["name"])
                players_data.append({
                    "player_name": b.name,
                    "is_bot": True,
                    "final_score": b.score,
                    "correct_answers": b.correct_answers,
                    "wrong_answers": b.wrong_answers,
                    "rank": rank,
                })

        game_data = {
            "num_humans": len(self.human_players),
            "num_bots": len(self.bot_players),
            "winner_name": winner["name"] if winner else None,
            "winner_score": winner["score"] if winner else None,
            "players": players_data,
            "answers": all_answers,
        }

        game_id = None
        try:
            game_id = await save_game_result(game_data)
        except Exception as e:
            print(f"[DB] Error saving game: {e}")

        await self.emit("game_over", {
            "leaderboard": scores,
            "winner": winner,
            "game_id": game_id,
        }, room=self.room_id)
