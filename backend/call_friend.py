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
        "You are a witty, enthusiastic trivia friend who just got a panicked phone call asking for help. "
        "You're smart but you never just give away the answer directly — you give a helpful hint, "
        "drop a fun fact related to the topic, and end with encouragement. "
        "Keep it under 3 sentences. Be warm, funny, and slightly dramatic. "
        "Speak in first person as if you're actually on the phone."
    ),
)


async def ask_friend(question: dict) -> str:
    """
    Ask the AI 'friend' for advice on the current question.
    Returns a short, fun hint string.
    """
    options = [question["correct"], question["wrong1"], question["wrong2"], question["wrong3"]]
    random.shuffle(options)
    options_text = ", ".join(f'"{o}"' for o in options)

    prompt = (
        f'My friend is stuck on this trivia question:\n'
        f'"{question["question"]}"\n'
        f'The options are: {options_text}\n'
        f'Give them a fun, helpful hint without revealing the answer directly!'
    )

    try:
        result = await friend_agent.run(prompt)
        return result.data
    except Exception as e:
        return (
            f"Hmm, that's a tough one! I'd think carefully about what you already know "
            f"about {question.get('category', 'this topic')}. You've got this! 🤞"
        )
