"""Interactive CLI chat interface for the e-commerce support agent."""

from __future__ import annotations

from src.agent import Agent


def main() -> None:
    print("ShopEasy Customer Support Agent")
    print("Type your message, or /quit to exit.\n")

    agent = Agent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "/q"):
            print("Goodbye!")
            break

        response = agent.run(user_input)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()
