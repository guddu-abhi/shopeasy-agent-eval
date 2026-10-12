"""Interactive CLI chat interface for the e-commerce support agent."""

from __future__ import annotations

import uuid

from src.agent import Agent


def main() -> None:
    print("ShopEasy Customer Support Agent")
    print("Type your message, or /quit to exit.\n")

    # One thread per chat session, so follow-up turns keep their context.
    agent = Agent(memory=True)
    thread_id = str(uuid.uuid4())

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

        response = agent.run(user_input, thread_id=thread_id)
        print(f"\nAgent: {response}\n")


if __name__ == "__main__":
    main()
