from core.planner import create_plan
from tools.registry import ToolRegistry
from tools.basic import calculator, text_analyzer


class OrbitAgent:

    def __init__(self):
        self.name = "ORBIT"

        self.tools = ToolRegistry()

        self.tools.register(
            "calculator",
            "Performs mathematical calculations.",
            calculator
        )

        self.tools.register(
            "text_analyzer",
            "Analyzes text length and word count.",
            text_analyzer
        )

    def run(self, goal):
        print(f"{self.name} received goal:")
        print(goal)

        plan = create_plan(goal)

        return {
            "goal": goal,
            "plan": plan,
            "available_tools": self.tools.list_tools()
        }


def run_agent(goal):
    agent = OrbitAgent()
    return agent.run(goal)
