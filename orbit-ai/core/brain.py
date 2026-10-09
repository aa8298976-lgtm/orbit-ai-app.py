
import os
from openai import OpenAI


SYSTEM_PROMPT = """
You are ORBIT AI.

You help the user understand goals, plan tasks,
use available tools, and evaluate results.

Never claim an action succeeded unless it did.
If an external service is unavailable, explain why.
"""


def ask_orbit(user_input):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return (
            "ORBIT is running in offline mode. "
            "The AI API key is not configured. "
            "Internal tools can still be used."
        )

    try:
        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="gpt-5",
            instructions=SYSTEM_PROMPT,
            input=user_input
        )

        return response.output_text

    except Exception as error:
        message = str(error).lower()

        if "insufficient_quota" in message or "credit_balance_exhausted" in message:
            return (
                "ORBIT is running, but the AI service has no API credits. "
                "Internal tools remain available."
            )

        if "rate_limit" in message or "429" in message:
            return (
                "ORBIT reached an API rate limit. "
                "Please try again later."
            )

        return (
            "ORBIT could not reach the AI service. "
            "Please check the connection and API settings."
        )
