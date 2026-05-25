"""
Step 3: Filter questions using a 'less smart' LLM (Gemini 2.5 Flash).
Questions that Gemini Flash cannot answer correctly are removed —
they're likely too obscure or ambiguous for a fun trivia game.

We ask the model to pick the correct answer from 4 options (A/B/C/D).
If it gets it wrong, we remove the question.
"""

import os
import json
import asyncio
import csv
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Use the new google-genai SDK with async client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Use Gemini 2.5 Flash as the "weaker" model (fast, capable, but not GPT-4o level)
WEAK_MODEL = "gemini-2.5-flash"
CONCURRENT_REQUESTS = 5   # Parallel batches
QUESTIONS_PER_PROMPT = 10  # Questions per API call


def shuffle_answers(question: dict) -> tuple[list[str], int]:
    """
    Shuffle the 4 answers randomly.
    Returns (shuffled_list, correct_index) where correct_index is 0-based.
    """
    answers = [
        question["correct"],
        question["wrong1"],
        question["wrong2"],
        question["wrong3"],
    ]
    indices = list(range(4))
    random.shuffle(indices)
    shuffled = [answers[i] for i in indices]
    correct_pos = indices.index(0)  # index 0 was the correct answer
    return shuffled, correct_pos


async def test_batch_of_questions(questions: list[dict], start_idx: int) -> list[bool]:
    """
    Test a batch of questions using Gemini Flash.
    Returns list of booleans: True = answered correctly, False = wrong.
    """
    batch_prompt_parts = []
    answer_keys = []

    for i, q in enumerate(questions):
        shuffled, correct_pos = shuffle_answers(q)
        letters = ["A", "B", "C", "D"]
        correct_letter = letters[correct_pos]
        answer_keys.append(correct_letter)

        options_text = "\n".join(f"  {letters[j]}) {shuffled[j]}" for j in range(4))
        batch_prompt_parts.append(
            f"Question {i+1}: {q['question']}\n{options_text}"
        )

    full_prompt = f"""Answer each trivia question by choosing A, B, C, or D.

{chr(10).join(batch_prompt_parts)}

Return a JSON object with key "answers" containing a list of letters (one per question, in order).
Example: {{"answers": ["A", "C", "B", "D"]}}
Return ONLY the JSON object, nothing else."""

    try:
        response = await client.aio.models.generate_content(
            model=WEAK_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )

        result_text = response.text.strip()
        parsed = json.loads(result_text)
        answers = parsed.get("answers", [])

        results = []
        for i, (given, expected) in enumerate(zip(answers, answer_keys)):
            correct = given.upper().strip() == expected
            results.append(correct)

        # Pad with False if fewer answers returned than expected
        while len(results) < len(questions):
            results.append(False)

        return results

    except Exception as e:
        print(f"    ⚠️  Error testing batch at Q{start_idx + 1}: {e}")
        # On error, keep all questions (benefit of the doubt)
        return [True] * len(questions)


async def test_all_questions(questions: list[dict]) -> list[bool]:
    """
    Test all questions in concurrent batches.
    Returns list of booleans (True = keep, False = remove).
    """
    all_results = [None] * len(questions)
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def test_batch_safe(batch: list[dict], start: int):
        async with semaphore:
            return await test_batch_of_questions(batch, start)

    # Build all tasks
    tasks = []
    batch_starts = []
    for start in range(0, len(questions), QUESTIONS_PER_PROMPT):
        batch = questions[start:start + QUESTIONS_PER_PROMPT]
        tasks.append(test_batch_safe(batch, start))
        batch_starts.append(start)

    print(f"  Testing {len(questions)} questions in {len(tasks)} batches (concurrent={CONCURRENT_REQUESTS})...")

    batch_results = await asyncio.gather(*tasks)

    for start, results in zip(batch_starts, batch_results):
        for i, result in enumerate(results):
            if start + i < len(all_results):
                all_results[start + i] = result

    return all_results


async def main():
    input_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_unique.csv')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_filtered.csv')

    # Load questions
    questions = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)

    print(f"🧪 Filtering {len(questions)} questions using {WEAK_MODEL}")
    print(f"   Strategy: Remove questions that {WEAK_MODEL} cannot answer correctly")
    print(f"   (These are likely too obscure or ambiguous for a fun trivia game)\n")

    results = await test_all_questions(questions)

    # Separate kept vs removed
    kept = [q for q, keep in zip(questions, results) if keep]
    removed = [q for q, keep in zip(questions, results) if not keep]

    # Stats by difficulty
    diff_stats = {}
    for q, keep in zip(questions, results):
        d = int(q.get("difficulty", 5))
        if d not in diff_stats:
            diff_stats[d] = {"kept": 0, "removed": 0}
        if keep:
            diff_stats[d]["kept"] += 1
        else:
            diff_stats[d]["removed"] += 1

    print(f"\n✅ Filtering complete:")
    print(f"   Original:  {len(questions)} questions")
    print(f"   Kept:      {len(kept)} (Gemini answered correctly)")
    print(f"   Removed:   {len(removed)} (Gemini got wrong → too hard/obscure)")
    print(f"\n   By difficulty:")
    for d in sorted(diff_stats.keys()):
        s = diff_stats[d]
        total = s["kept"] + s["removed"]
        pct = s["kept"] / total * 100 if total > 0 else 0
        print(f"     Difficulty {d:2d}: kept {s['kept']}/{total} ({pct:.0f}%)")

    if len(kept) < 250:
        print(f"\n⚠️  WARNING: Only {len(kept)} questions remain (need 250+).")
        print(f"   Consider re-running generate_questions.py to add more questions.")
    else:
        print(f"\n✓ Have {len(kept)} questions — meets the 250+ requirement!")

    # Save filtered questions
    if kept:
        fieldnames = list(kept[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(kept)
        print(f"💾 Saved to: {output_path}")

    # Save removed questions for reference
    if removed:
        removed_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_removed.csv')
        fieldnames = list(removed[0].keys())
        with open(removed_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(removed)
        print(f"📋 Removed questions saved to: {removed_path}")


if __name__ == "__main__":
    asyncio.run(main())
