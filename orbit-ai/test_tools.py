
from core.agent import OrbitAgent


def main():
    print("=== ORBIT OFFLINE TOOLS TEST ===")

    agent = OrbitAgent()

    print("\n1. Available tools:")
    print(agent.tools.list_tools())

    print("\n2. Calculator:")
    print(
        agent.use_tool(
            "calculator",
            expression="25 * 4 + 10"
        )
    )

    print("\n3. Text analyzer:")
    print(
        agent.use_tool(
            "text_analyzer",
            text="ORBIT is an open world AI."
        )
    )

    print("\n4. Memory:")
    agent.memory.add(
        "Offline tools test completed.",
        memory_type="system_test"
    )
    print(agent.get_memory())

    print("\n=== TEST FINISHED ===")


if __name__ == "__main__":
    main()
