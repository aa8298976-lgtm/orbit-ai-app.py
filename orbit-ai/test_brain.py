
from core.brain import ask_orbit


def main():
    print("=== ORBIT BRAIN TEST ===")

    result = ask_orbit(
        "Reply in Persian with one short sentence confirming that ORBIT is connected."
    )

    print("\nAI response:")
    print(result)


if __name__ == "__main__":
    main()

