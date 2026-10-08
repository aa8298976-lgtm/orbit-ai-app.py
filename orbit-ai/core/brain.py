import os
from openai import OpenAI


SYSTEM_PROMPT = """
You are ORBIT AI.

You are an intelligent, goal-oriented AI agent.

Your responsibilities:

1. Understand the user's goal.
2. Break complex goals into logical steps.
3. Create practical plans.
4. Identify the tools required.
5. Evaluate results.
6. Detect mistakes and propose corrections.
7. Never claim that an action was completed unless it actually happened.
8. Never invent information, files, sources, or tool results.
9. Ask for user approval before sensitive external actions.

You are designed to become a modular open-world AI system.
"""


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(api_key=api_key)


def ask_orbit(user_input):

    client = get_client()

    response = client.responses.create(
        model="gpt-5",
        instructions=SYSTEM_PROMPT,
        input=user_input
    )

    return response.output_text
