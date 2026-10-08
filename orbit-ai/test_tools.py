from core.agent import OrbitAgent


def main():
    print("=== ORBIT SYSTEM TEST ===")

    agent = OrbitAgent()

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

    print("\nMemory test:")

    agent.memory.add(
        "ORBIT system test completed.",
        memory_type="system_test"
    )

    print(agent.get_memory())


if __name__ == "__main__":
    main()
