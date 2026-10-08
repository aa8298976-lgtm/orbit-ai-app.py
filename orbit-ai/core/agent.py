from core.planner import create_plan


class OrbitAgent:

    def __init__(self):
        self.name = "ORBIT"

    def run(self, goal):
        print(f"{self.name} received goal:")
        print(goal)

        plan = create_plan(goal)

        return {
            "goal": goal,
            "plan": plan
        }


def run_agent(goal):
    agent = OrbitAgent()
    return agent.run(goal)
