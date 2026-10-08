from core.brain import ask_orbit


def create_plan(goal):
    prompt = f"""
You are the planning module of ORBIT AI.

User goal:
{goal}

Create a clear execution plan.

Return exactly these sections:

GOAL:
Describe the goal briefly.

STEPS:
Create numbered steps from beginning to end.

TOOLS:
List the tools or capabilities that may be required.

RISKS:
List important risks or uncertainties.

SUCCESS CRITERIA:
Explain how we will know the goal was successfully completed.
"""

    return ask_orbit(prompt)
