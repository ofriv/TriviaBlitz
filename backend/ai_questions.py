"""
AI-generated trivia questions using GPT-4o-mini.

Called when a player selects "Custom Topic" mode on the landing screen.
Returns 10 trivia questions in the same dict format as the database uses.
"""

import os
import json

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def generate_questions(topic: str, count: int = 10) -> list[dict]:
    """
    Generate `count` trivia questions about `topic` using GPT-4o-mini.

    Returns a list of question dicts with the same schema as DB rows:
      {id, question, correct, wrong1, wrong2, wrong3, difficulty, category}

    IDs are negative to distinguish AI questions from DB questions.
    Raises ValueError / openai.APIError on failure — callers should
    catch and fall back to DB questions.
    """

    prompt = (
        f'Generate exactly {count} trivia questions about: "{topic}"\n\n'
        "Return ONLY a valid JSON array. Each element must be an object "
        "with exactly these keys:\n"
        '  "question"   — the trivia question text (ends with ?)\n'
        '  "correct"    — the single correct answer (concise, 1-6 words)\n'
        '  "wrong1"     — a plausible but incorrect distractor\n'
        '  "wrong2"     — a plausible but incorrect distractor\n'
        '  "wrong3"     — a plausible but incorrect distractor\n'
        '  "difficulty" — integer 1-10 (1=trivial, 10=expert)\n'
        f'  "category"   — short category label (the topic name)\n\n'
        "Requirements:\n"
        "- Every question must have exactly ONE factually correct answer\n"
        "- Wrong answers must be plausible distractors, not obvious nonsense\n"
        "- Vary the difficulty: include easy (1-4), medium (5-6), and hard (7-9) questions\n"
        "- Questions should cover diverse aspects of the topic\n"
        "- Return ONLY the JSON array — no explanation, no markdown fences"
    )

    response = await _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a trivia question generator. Return only valid JSON arrays as instructed.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content.strip()

    # GPT with json_object mode wraps the array in an object — unwrap it
    parsed = json.loads(text)
    if isinstance(parsed, dict):
        # Find the first list value
        raw = next((v for v in parsed.values() if isinstance(v, list)), None)
        if raw is None:
            raise ValueError(f"No list found in GPT JSON response: {text[:300]}")
    else:
        raw = parsed  # already a list

    questions: list[dict] = []
    for i, q in enumerate(raw[:count]):
        required = ("question", "correct", "wrong1", "wrong2", "wrong3")
        if not all(k in q for k in required):
            print(f"[AI Questions] Skipping malformed question #{i}: {q}")
            continue
        questions.append({
            "id":         -(i + 1),              # negative → AI-generated
            "question":   str(q["question"]),
            "correct":    str(q["correct"]),
            "wrong1":     str(q["wrong1"]),
            "wrong2":     str(q["wrong2"]),
            "wrong3":     str(q["wrong3"]),
            "difficulty": max(1, min(10, int(q.get("difficulty", 5)))),
            "category":   str(q.get("category", topic)),
        })

    if not questions:
        raise ValueError("GPT returned no valid questions")

    print(f"[AI Questions] Parsed {len(questions)}/{count} questions for topic: '{topic}'")
    return questions
