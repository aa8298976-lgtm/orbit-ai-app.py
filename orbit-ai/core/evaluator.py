from core.brain import ask_orbit


def evaluate_result(goal, result):
    prompt = f"""
You are the evaluation module of ORBIT AI.

USER GOAL:
{goal}

RESULT:
{result}

Evaluate the result objectively.

Return exactly:

STATUS:
SUCCESS, PARTIAL, or FAILED

QUALITY:
A score from 0 to 100.

WHAT WORKED:
What was done correctly.

WHAT IS MISSING:
What is incomplete or incorrect.

NEXT ACTION:
What ORBIT should do next.

IMPORTANT:
Do not claim that something was completed unless the provided result proves it.
"""

    return ask_orbit(prompt)
