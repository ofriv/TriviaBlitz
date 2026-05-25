"""
Master pipeline runner.
Runs all 4 steps in sequence to go from nothing → trivia.db

Usage:
    python run_pipeline.py              # Run all steps
    python run_pipeline.py --from 2     # Start from step 2 (skip generation)
    python run_pipeline.py --only 4     # Run only step 4 (build DB from existing CSV)
"""
import sys
import io
# Fix Windows terminal encoding for emoji/unicode output
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
import argparse
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))


async def step1_generate():
    print("\n" + "="*60)
    print("STEP 1: Generating questions with GPT-4o")
    print("="*60)
    from generate_questions import main
    await main()


async def step2_verify():
    print("\n" + "="*60)
    print("STEP 2: Verifying uniqueness with GPT-4o")
    print("="*60)
    from verify_uniqueness import main
    await main()


async def step3_filter():
    print("\n" + "="*60)
    print("STEP 3: Filtering with Gemini Flash (weak model test)")
    print("="*60)
    from filter_questions import main
    await main()


async def step4_build_db():
    print("\n" + "="*60)
    print("STEP 4: Building SQLite database")
    print("="*60)
    from build_database import build_database
    await build_database()


async def main():
    parser = argparse.ArgumentParser(description="Trivia question pipeline")
    parser.add_argument("--from", dest="from_step", type=int, default=1,
                        help="Start from this step (1-4)")
    parser.add_argument("--only", dest="only_step", type=int, default=None,
                        help="Run only this step")
    args = parser.parse_args()

    steps = {
        1: step1_generate,
        2: step2_verify,
        3: step3_filter,
        4: step4_build_db,
    }

    print("🎮 Trivia Question Pipeline")
    print("="*60)

    # Check .env exists
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        print(f"   Create {env_path} with your API keys:")
        print("   OPENAI_API_KEY=...")
        print("   GOOGLE_API_KEY=...")
        sys.exit(1)

    if args.only_step:
        if args.only_step not in steps:
            print(f"❌ Invalid step: {args.only_step}. Choose 1-4.")
            sys.exit(1)
        await steps[args.only_step]()
    else:
        start = args.from_step
        for step_num in range(start, 5):
            await steps[step_num]()

    print("\n" + "="*60)
    print("✅ Pipeline complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
