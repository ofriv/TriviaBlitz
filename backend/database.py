"""
Database layer for the trivia game backend.
Handles all async SQLite operations: fetching questions, saving game results, player stats.
"""

import os
import asyncio
import aiosqlite
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trivia.db')


async def get_db():
    """Get a database connection."""
    return await aiosqlite.connect(DB_PATH)


async def fetch_questions(difficulty: int = None, category: str = None, limit: int = 10, exclude_ids: list = None) -> list[dict]:
    """
    Fetch random questions from the database.
    Optionally filter by difficulty and/or category.
    Optionally exclude already-used question IDs.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        conditions = []
        params = []

        if difficulty is not None:
            conditions.append("difficulty = ?")
            params.append(difficulty)

        if category is not None:
            conditions.append("category = ?")
            params.append(category)

        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            conditions.append(f"id NOT IN ({placeholders})")
            params.extend(exclude_ids)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)

        cursor = await db.execute(
            f"SELECT * FROM questions {where} ORDER BY RANDOM() LIMIT ?",
            params
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def fetch_question_by_difficulty_range(min_diff: int, max_diff: int, exclude_ids: list = None) -> dict | None:
    """
    Fetch a single random question within a difficulty range.
    Used for adaptive difficulty selection.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        params = [min_diff, max_diff]
        exclude_clause = ""

        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            exclude_clause = f"AND id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        cursor = await db.execute(
            f"""SELECT * FROM questions
                WHERE difficulty BETWEEN ? AND ?
                {exclude_clause}
                ORDER BY RANDOM() LIMIT 1""",
            params
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def save_game_result(game_data: dict) -> int:
    """
    Save a completed game to the database.
    Returns the new game_id.

    game_data keys:
      - num_humans, num_bots
      - winner_name, winner_score
      - players: list of {player_name, is_bot, final_score, correct_answers, wrong_answers, rank}
      - answers: list of {player_name, question_id, question_order, answer_given, is_correct, time_taken_ms, points_earned, powerup_used}
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Insert game record
        cursor = await db.execute(
            """INSERT INTO games (ended_at, num_humans, num_bots, winner_name, winner_score)
               VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?)""",
            (game_data["num_humans"], game_data["num_bots"],
             game_data.get("winner_name"), game_data.get("winner_score"))
        )
        game_id = cursor.lastrowid

        # Insert player records
        for player in game_data.get("players", []):
            await db.execute(
                """INSERT INTO game_players (game_id, player_name, is_bot, final_score, correct_answers, wrong_answers, rank)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (game_id, player["player_name"], player["is_bot"],
                 player["final_score"], player["correct_answers"],
                 player["wrong_answers"], player["rank"])
            )

        # Insert answer records
        for ans in game_data.get("answers", []):
            await db.execute(
                """INSERT INTO game_answers (game_id, player_name, question_id, question_order,
                   answer_given, is_correct, time_taken_ms, points_earned, powerup_used)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (game_id, ans["player_name"], ans["question_id"], ans["question_order"],
                 ans.get("answer_given"), ans["is_correct"], ans.get("time_taken_ms"),
                 ans.get("points_earned", 0), ans.get("powerup_used"))
            )

        # Update question_stats
        for ans in game_data.get("answers", []):
            await db.execute(
                """UPDATE question_stats
                   SET times_shown = times_shown + 1,
                       times_correct = times_correct + ?,
                       avg_time_ms = (avg_time_ms * times_shown + ?) / (times_shown + 1),
                       last_shown = CURRENT_TIMESTAMP
                   WHERE question_id = ?""",
                (1 if ans["is_correct"] else 0,
                 ans.get("time_taken_ms", 0),
                 ans["question_id"])
            )

        # Update player_stats (upsert)
        for player in game_data.get("players", []):
            if player["is_bot"]:
                continue  # Don't track bot stats
            is_winner = player["player_name"] == game_data.get("winner_name")
            await db.execute(
                """INSERT INTO player_stats (player_name, games_played, games_won, total_score,
                   total_correct, total_questions, best_score, last_played)
                   VALUES (?, 1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(player_name) DO UPDATE SET
                     games_played = games_played + 1,
                     games_won = games_won + ?,
                     total_score = total_score + ?,
                     total_correct = total_correct + ?,
                     total_questions = total_questions + ?,
                     best_score = MAX(best_score, ?),
                     last_played = CURRENT_TIMESTAMP""",
                (player["player_name"],
                 1 if is_winner else 0,
                 player["final_score"],
                 player["correct_answers"],
                 player["correct_answers"] + player["wrong_answers"],
                 player["final_score"],
                 # ON CONFLICT values:
                 1 if is_winner else 0,
                 player["final_score"],
                 player["correct_answers"],
                 player["correct_answers"] + player["wrong_answers"],
                 player["final_score"])
            )

        await db.commit()
        return game_id


async def get_player_stats(player_name: str) -> dict | None:
    """Get lifetime stats for a player."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM player_stats WHERE player_name = ?",
            (player_name,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_leaderboard(limit: int = 10) -> list[dict]:
    """Get top players by total score."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT player_name, games_played, games_won, total_score, best_score,
                      CASE WHEN total_questions > 0
                           THEN ROUND(total_correct * 100.0 / total_questions, 1)
                           ELSE 0 END as accuracy_pct
               FROM player_stats
               ORDER BY total_score DESC
               LIMIT ?""",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
