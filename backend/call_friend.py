"""
Call-a-Friend power-up implementation using PydanticAI.

This calls GPT-4o-mini and returns a fun, in-character hint for the current question.
The "friend" has a fun personality — they're helpful but a little dramatic about it.
"""

import os
import random
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Build the model using an explicit OpenAI client so we can pass our API key
_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
_provider = OpenAIProvider(openai_client=_openai_client)
model = OpenAIModel("gpt-4o-mini", provider=_provider)

friend_agent = Agent(
    model,
    system_prompt=(
        "You are a knowledgeable trivia friend taking a phone call. "
        "Give ONE specific, concrete clue that genuinely helps identify the correct answer — "
        "a real fact, a memory trick, or a key detail that points toward it. "
        "Do NOT just mention the category name or say 'think hard'. "
        "Do NOT reveal the exact answer word-for-word. "
        "Keep it to 1-2 short sentences. Be direct and helpful."
    ),
)


async def ask_friend(question: dict) -> str:
    """
    Ask the AI 'friend' for advice on the current question.
    Returns a short, concrete hint string.
    """
    options = [question["correct"], question["wrong1"], question["wrong2"], question["wrong3"]]
    random.shuffle(options)
    options_text = " / ".join(options)

    prompt = (
        f'Question: {question["question"]}\n'
        f'Options: {options_text}\n'
        f'Give a specific clue or fact that helps identify the correct answer '
        f'(without saying the answer outright).'
    )

    try:
        result = await friend_agent.run(prompt)
        return result.data
    except Exception as e:
        print(f"[call_friend] error: {e}")
        return "I'd focus on eliminating the obviously wrong ones first — trust your gut on the rest! 🤞"
