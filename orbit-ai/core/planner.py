
from core.brain import ask_orbit


def create_plan(goal):
    goal = goal.strip()

    if not goal:
        return {
            "mode": "offline",
            "goal": "",
            "steps": [],
            "message": "Please provide a goal."
        }

    # Try the AI planner first.
    result = ask_orbit(
        f"""
Create a practical plan for this goal:
{goal}

Return:
1. Goal
2. Numbered steps
3. Required tools
4. Risks
5. Success criteria
"""
    )

    # If the AI service is unavailable, use a basic offline plan.
    if result.startswith("ORBIT is running") or result.startswith(
        "ORBIT could not"
    ):
        return {
            "mode": "offline",
            "goal": goal,
            "steps": [
                f"Understand the goal: {goal}",
                "Break the goal into smaller tasks.",
                "Identify the tools and information required.",
                "Execute each task and record the results.",
                "Review the results and identify what remains."
            ],
            "message": "Offline plan created. Steps are generic and may need customization."
        }

    return {
        "mode": "ai",
        "goal": goal,
        "plan": result
    }
