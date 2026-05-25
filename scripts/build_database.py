"""
Step 4: Convert the filtered questions CSV into a SQLite database.
Also creates tables for game sessions, player stats, and analytics.
"""

import os
import csv
import asyncio
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trivia.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_filtered.csv')

CREATE_TABLES_SQL = """
-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question    TEXT NOT NULL,
    correct     TEXT NOT NULL,
    wrong1      TEXT NOT NULL,
    wrong2      TEXT NOT NULL,
    wrong3      TEXT NOT NULL,
    difficulty  INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 10),
    category    TEXT NOT NULL
);

-- Game sessions
CREATE TABLE IF NOT EXISTS games (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    ended_at        DATETIME,
    num_humans      INTEGER DEFAULT 0,
    num_bots        INTEGER DEFAULT 0,
    winner_name     TEXT,
    winner_score    INTEGER
);

-- Players in each game
CREATE TABLE IF NOT EXISTS game_players (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER NOT NULL REFERENCES games(id),
    player_name     TEXT NOT NULL,
    is_bot          BOOLEAN NOT NULL DEFAULT 0,
    final_score     INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    wrong_answers   INTEGER DEFAULT 0,
    rank            INTEGER
);

-- Individual question answers per game
CREATE TABLE IF NOT EXISTS game_answers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id         INTEGER NOT NULL REFERENCES games(id),
    player_name     TEXT NOT NULL,
    question_id     INTEGER NOT NULL REFERENCES questions(id),
    question_order  INTEGER NOT NULL,
    answer_given    TEXT,
    is_correct      BOOLEAN,
    time_taken_ms   INTEGER,
    points_earned   INTEGER DEFAULT 0,
    powerup_used    TEXT  -- 'fifty_fifty', 'call_friend', 'double_score', or NULL
);

-- Player lifetime stats (across all games)
CREATE TABLE IF NOT EXISTS player_stats (
    player_name     TEXT PRIMARY KEY,
    games_played    INTEGER DEFAULT 0,
    games_won       INTEGER DEFAULT 0,
    total_score     INTEGER DEFAULT 0,
    total_correct   INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    best_score      INTEGER DEFAULT 0,
    last_played     DATETIME
);

-- Per-question stats (for analytics)
CREATE TABLE IF NOT EXISTS question_stats (
    question_id         INTEGER PRIMARY KEY REFERENCES questions(id),
    times_shown         INTEGER DEFAULT 0,
    times_correct       INTEGER DEFAULT 0,
    avg_time_ms         REAL DEFAULT 0,
    last_shown          DATETIME
);
"""


async def build_database():
    print(f"🏗️  Building SQLite database: {DB_PATH}")

    # Remove existing DB if present
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("  ♻️  Removed existing database")

    async with aiosqlite.connect(DB_PATH) as db:
        # Create all tables
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
        print("  ✓ Created all tables")

        # Load questions from CSV
        if not os.path.exists(CSV_PATH):
            print(f"  ✗ CSV not found: {CSV_PATH}")
            print("  Run the generation pipeline first!")
            return

        questions = []
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                questions.append(row)

        print(f"  📄 Loading {len(questions)} questions from CSV...")

        # Insert questions
        insert_sql = """
            INSERT INTO questions (question, correct, wrong1, wrong2, wrong3, difficulty, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        for q in questions:
            await db.execute(insert_sql, (
                q["question"],
                q["correct"],
                q["wrong1"],
                q["wrong2"],
                q["wrong3"],
                int(q.get("difficulty", 5)),
                q.get("category", "General"),
            ))

        await db.commit()

        # Initialize question_stats for all questions
        await db.execute("""
            INSERT INTO question_stats (question_id)
            SELECT id FROM questions
        """)
        await db.commit()

        # Count by difficulty
        cursor = await db.execute("""
            SELECT difficulty, COUNT(*) as cnt
            FROM questions
            GROUP BY difficulty
            ORDER BY difficulty
        """)
        rows = await cursor.fetchall()

        print(f"\n✅ Database built successfully!")
        print(f"   Total questions: {len(questions)}")
        print(f"\n   Distribution by difficulty:")
        for difficulty, count in rows:
            bar = "█" * (count // 2)
            print(f"     {difficulty:2d} │ {bar} {count}")

        print(f"\n💾 Database saved to: {DB_PATH}")


if __name__ == "__main__":
    asyncio.run(build_database())
