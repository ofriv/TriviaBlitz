"""
Step 2: Use GPT-4o to verify all questions are unique (no duplicates or near-duplicates).
Processes questions in batches and removes any that are too similar to each other.
"""

import os
import json
import asyncio
import csv
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEDUP_BATCH_SIZE = 50  # Check 50 questions at a time for duplicates


async def find_duplicates_in_batch(questions: list[dict], batch_num: int) -> list[int]:
    """
    Ask GPT-4o to identify duplicate/near-duplicate question indices within a batch.
    Returns indices (0-based) of questions to REMOVE.
    """
    # Create a numbered list of just the question texts
    numbered = "\n".join(f"{i}. {q['question']}" for i, q in enumerate(questions))

    prompt = f"""Review these trivia questions and identify any duplicates or near-duplicates (same topic asked in very similar ways).

{numbered}

Return a JSON object with one field "remove_indices" containing a list of integer indices (0-based)
of questions to REMOVE (keep the first occurrence of any duplicate pair).
If no duplicates found, return {{"remove_indices": []}}.
Return ONLY the JSON object."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a trivia quality controller checking for duplicate questions. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        to_remove = result.get("remove_indices", [])
        # Validate indices are in range
        to_remove = [i for i in to_remove if 0 <= i < len(questions)]
        print(f"  Batch {batch_num}: Found {len(to_remove)} duplicates to remove")
        return to_remove
    except Exception as e:
        print(f"  ⚠️  Error checking batch {batch_num}: {e}")
        return []


async def cross_check_duplicates(all_questions: list[dict]) -> list[int]:
    """
    After intra-batch deduplication, do a cross-batch check by sending
    summaries of all question topics to GPT-4o.
    Returns global indices to remove.
    """
    print("\n  Cross-checking all questions for global duplicates...")
    numbered = "\n".join(f"{i}. {q['question']}" for i, q in enumerate(all_questions))

    # Split into chunks of 100 for the cross-check
    all_to_remove = set()

    chunk_size = 100
    for start in range(0, len(all_questions), chunk_size):
        chunk = all_questions[start:start + chunk_size]
        chunk_numbered = "\n".join(
            f"{start + i}. {q['question']}" for i, q in enumerate(chunk)
        )
        prompt = f"""These are trivia questions from a larger set (indices {start} to {start + len(chunk) - 1}).
Identify any that are clearly duplicates of each other within this chunk.

{chunk_numbered}

Return JSON: {{"remove_indices": [list of global integer indices to remove]}}
Only return indices of duplicates (keep the first occurrence). Return ONLY the JSON."""

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You check for duplicate trivia questions. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            result = json.loads(response.choices[0].message.content)
            to_remove = result.get("remove_indices", [])
            to_remove = [i for i in to_remove if start <= i < start + len(chunk)]
            all_to_remove.update(to_remove)
            print(f"  Cross-check chunk {start}-{start+len(chunk)-1}: {len(to_remove)} more duplicates")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️  Cross-check error: {e}")

    return list(all_to_remove)


async def main():
    input_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_raw.csv')
    output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'questions_unique.csv')

    # Load questions
    questions = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)

    print(f"🔍 Checking {len(questions)} questions for duplicates using GPT-4o")
    print(f"   Input: {input_path}\n")

    indices_to_remove = set()

    # Step 1: Intra-batch deduplication
    print("Step 1: Intra-batch deduplication")
    for batch_num, start in enumerate(range(0, len(questions), DEDUP_BATCH_SIZE)):
        batch = questions[start:start + DEDUP_BATCH_SIZE]
        local_indices = await find_duplicates_in_batch(batch, batch_num + 1)
        # Convert local indices to global indices
        global_indices = [start + i for i in local_indices]
        indices_to_remove.update(global_indices)
        await asyncio.sleep(0.5)

    print(f"\nStep 1 done. Marked {len(indices_to_remove)} for removal.")

    # Step 2: Cross-batch check
    remaining = [q for i, q in enumerate(questions) if i not in indices_to_remove]
    print(f"\nStep 2: Cross-batch check on remaining {len(remaining)} questions")
    cross_remove = await cross_check_duplicates(remaining)

    # Map cross_remove indices back to original
    remaining_indices = [i for i in range(len(questions)) if i not in indices_to_remove]
    for local_idx in cross_remove:
        if local_idx < len(remaining_indices):
            indices_to_remove.add(remaining_indices[local_idx])

    # Filter questions
    unique_questions = [q for i, q in enumerate(questions) if i not in indices_to_remove]

    print(f"\n✅ Uniqueness check complete:")
    print(f"   Original:  {len(questions)} questions")
    print(f"   Removed:   {len(indices_to_remove)} duplicates")
    print(f"   Remaining: {len(unique_questions)} unique questions")

    # Save
    if unique_questions:
        fieldnames = list(unique_questions[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_questions)
        print(f"💾 Saved to: {output_path}")
    else:
        print("⚠️  No questions remaining after deduplication!")


if __name__ == "__main__":
    asyncio.run(main())
