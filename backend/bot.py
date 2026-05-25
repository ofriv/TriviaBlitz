"""
Bot player logic.

Bots are added when only 1 human joins (1-3 bots).
Behavior:
  - Answer after a realistic human-like delay (3-15 seconds)
  - ~72% accuracy overall, scaled by difficulty (easy = high accuracy, hard = low)
  - Never answer in under 2 seconds (unrealistically fast)
  - Personality names so they feel like real players
"""

import asyncio
import random

BOT_NAMES = [
    "QuizMaster_3000", "TriviaNerd", "BrainBot", "KnowledgeKing",
    "EinsteinBot", "WisdomWizard", "FactFinder", "QuizQueen",
    "SmartCookie", "BrainiacBot"
]

# Accuracy by difficulty level (1=easy → 10=hard)
ACCURACY_BY_DIFFICULTY = {
    1: 0.95, 2: 0.90, 3: 0.85, 4: 0.80, 5: 0.72,
    6: 0.62, 7: 0.50, 8: 0.38, 9: 0.28, 10: 0.18,
}


class BotPlayer:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self.streak = 0
        self.best_streak = 0
        # Each bot gets 3 power-ups (they never use them — keeps it simple)
        self.powerups_remaining = {"fifty_fifty": 1, "call_friend": 1, "double_score": 1}

    def decide_answer(self, question: dict) -> tuple[str, float]:
        """
        Decide what answer the bot gives and how long it 'thinks'.
        Returns (answer_text, delay_seconds).

        The answer is either the correct one or a random wrong one.
        """
        difficulty = question.get("difficulty", 5)
        accuracy = ACCURACY_BY_DIFFICULTY.get(difficulty, 0.65)

        # Thinking time: harder questions → bot thinks longer
        min_delay = 2.5 + difficulty * 0.3   # 2.8s for diff 1 → 5.5s for diff 10
        max_delay = 8.0 + difficulty * 0.7   # 8.7s for diff 1 → 15.0s for diff 10
        delay = random.uniform(min_delay, max_delay)

        # Decide: correct or wrong?
        if random.random() < accuracy:
            answer = question["correct"]
        else:
            wrongs = [question["wrong1"], question["wrong2"], question["wrong3"]]
            answer = random.choice(wrongs)

        return answer, delay

    def add_score(self, points: int, correct: bool):
        self.score += points
        if correct:
            self.correct_answers += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
        else:
            self.wrong_answers += 1
            self.streak = 0


def create_bots(num_bots: int) -> list[BotPlayer]:
    """Create 1-3 bot players with unique names."""
    names = random.sample(BOT_NAMES, min(num_bots, len(BOT_NAMES)))
    return [BotPlayer(name) for name in names]


def calculate_bot_count(num_humans: int) -> int:
    """
    If only 1 human, add 1-3 bots.
    If 2+ humans, no bots needed.
    """
    if num_humans == 1:
        return random.randint(1, 3)
    return 0
