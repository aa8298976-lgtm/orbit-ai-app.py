from core.agent import OrbitAgent


agent = OrbitAgent()

print("=== ORBIT TOOL TEST ===")

print("\nAvailable tools:")
print(agent.tools.list_tools())

print("\nCalculator test:")
print(
    agent.use_tool(
        "calculator",
        expression="25 * 4 + 10"
    )
)

print("\nText analyzer test:")
print(
    agent.use_tool(
        "text_analyzer",
        text="ORBIT is an open world AI."
    )
)
