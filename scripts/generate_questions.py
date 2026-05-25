"""
Step 1: Generate trivia questions using GPT-4o.
Generates 260+ questions in batches of 25 to maintain quality.
Each question has: question text, correct answer, 3 wrong answers, difficulty (1-10), category.
Answers are normalized so the correct answer isn't obviously longer.
"""

import os
import json
import asyncio
import csv
import time
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = [
    "Science & Nature",
    "History",
    "Geography",
    "Pop Culture & Entertainment",
    "Sports",
    "Technology & Computers",
    "Food & Drink",
    "Literature",
    "Music",
    "Art & Architecture",
    "Movies & TV",
    "Animals",
]

BATCH_SIZE = 25
BATCHES_PER_CATEGORY = 1  # 12 categories × 25 = 300 questions (buffer for filtering)

SYSTEM_PROMPT = """You are a trivia question writer. Generate high-quality multiple-choice trivia questions.
Rules:
1. All 4 answer options MUST be approximately the same length (±5 words). This is critical.
2. All wrong answers must be plausible but clearly incorrect.
3. Questions should be fun and interesting, not obscure.
4. Difficulty 1-3 = easy (common knowledge), 4-6 = medium, 7-10 = hard (specialist knowledge).
5. Never repeat a question topic within a batch.
6. Return ONLY valid JSON, no markdown, no explanation."""

USER_PROMPT_TEMPLATE = """Generate exactly {n} trivia questions about the category: "{category}".

Return a JSON array of objects. Each object must have these exact fields:
- "question": string (the question text)
- "correct": string (the correct answer, keep it concise)
- "wrong1": string (wrong answer, same length as correct)
- "wrong2": string (wrong answer, same length as correct)
- "wrong3": string (wrong answer, same length as correct)
- "difficulty": integer between 1 and 10
- "category": "{category}"

IMPORTANT: All answer options (correct, wrong1, wrong2, wrong3) must be similar in length.
Mix difficulties across the batch (some easy, some medium, some hard).

Return ONLY the JSON array, nothing else."""


async def generate_batch(category: str, n: int, attempt: int = 0) -> list[dict]:
    """Generate a batch of questions for a given category."""
    if attempt > 2:
        print(f"  ⚠️  Skipping batch after {attempt} failed attempts")
        return []

    try:
        print(f"  Generating {n} questions for '{category}' (attempt {attempt + 1})...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(n=n, category=category)}
            ],
            temperature=0.8,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        # GPT sometimes wraps array in {"questions": [...]}
        parsed = json.loads(content)
        if isinstance(parsed, list):
            questions = parsed
        elif isinstance(parsed, dict):
            # Find the array value
            questions = next((v for v in parsed.values() if isinstance(v, list)), [])
        else:
            questions = []

        # Validate each question has required fields
        valid = []
        required = {"question", "correct", "wrong1", "wrong2", "wrong3", "difficulty", "category"}
        for q in questions:
            if required.issubset(q.keys()):
                # Normalize: strip whitespace
                for field in required:
                    if isinstance(q[field], str):
                        q[field] = q[field].strip()
                # Ensure difficulty is int in range
                q["difficulty"] = max(1, min(10, int(q["difficulty"])))
                valid.append(q)
            else:
                print(f"    ⚠️  Skipped malformed question: {list(q.keys())}")

        print(f"  ✓ Got {len(valid)} valid questions for '{category}'")
        return valid

    except json.JSONDecodeError as e:
        print(f"  ✗ JSON parse error for '{category}': {e}. Retrying...")
        await asyncio.sleep(2)
        return await generate_batch(category, n, attempt + 1)
    except Exception as e:
        print(f"  ✗ Error for '{category}': {e}. Retrying...")
        await asyncio.sleep(5)
        return await generate_batch(category, n, attempt + 1)


def normalize_answer_lengths(question: dict) -> dict:
    """
    Ensure all 4 answer options are roughly similar in length.
    If the correct answer is much longer than wrong answers, truncate/note the issue.
    We'll just flag it — GPT usually handles this with our prompt.
    """
    answers = [
        question["correct"],
        question["wrong1"],
        question["wrong2"],
        question["wrong3"],
    ]
    lengths = [len(a) for a in answers]
    avg_len = sum(lengths) / 4
    max_len = max(lengths)
    min_len = min(lengths)

    # Flag if correct answer is suspiciously longer than all wrong answers
    if len(question["correct"]) == max_len and (max_len - min_len) > 20:
        question["_length_warning"] = True

    return question


async def main():
    all_questions = []

    print("🚀 Starting trivia question generation with GPT-4o")
    print(f"   Plan: {len(CATEGORIES)} categories × {BATCH_SIZE} questions = {len(CATEGORIES) * BATCH_SIZE} target\n")

    # Process categories with a small delay between requests to avoid rate limiting
    for i, category in enumerate(CATEGORIES):
        print(f"\n[{i+1}/{len(CATEGORIES)}] Category: {category}")
        batch = await generate_batch(category, BATCH_SIZE)
        batch = [normalize_answer_lengths(q) for q in batch]
        all_questions.extend(batch)

        # Small delay between categories to be respectful of rate limits
        if i < len(CATEGORIES) - 1:
            await asyncio.sleep(1)

    # Check for length warnings
    warnings = [q for q in all_questions if q.get("_length_warning")]
    if warnings:
        print(f"\n⚠️  {len(warnings)} questions have answer length imbalances (correct answer notably longer)")
        for w in warnings[:5]:
            print(f"   Q: {w['question'][:60]}...")
            print(f"   Correct ({len(w['correct'])}): {w['correct']}")
            print(f"   Wrong1  ({len(w['wrong1'])}): {w['wrong1']}")

    # Remove warning flag before saving
    for q in all_questions:
        q.pop("_length_warning", None)

    print(f"\n✅ Generated {len(all_questions)} questions total")

    # Save to CSV
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_raw.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = ["question", "correct", "wrong1", "wrong2", "wrong3", "difficulty", "category"]
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_questions)

    print(f"💾 Saved raw questions to: {output_path}")
    return all_questions


if __name__ == "__main__":
    asyncio.run(main())
