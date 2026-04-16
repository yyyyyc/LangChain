"""
main.py
Entry point for the company chatbot.
Run:  python main.py
"""

import os
from dotenv import load_dotenv
from agent import build_agent


def main():
    load_dotenv()
    os.environ.setdefault("LANGSMITH_TRACING", "false")  # silence warning when key is absent

    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set. Please edit .env and add your key.")
        return

    print("=" * 60)
    print("  Company HR Chatbot")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    print("\nInitializing agent (loading DB + PDF)...", flush=True)
    agent_executor = build_agent()
    print("Agent ready!\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue

        if question.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        try:
            result = agent_executor.invoke({"input": question})
            print(f"\nAssistant: {result['output']}\n")
        except Exception as e:
            print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    main()
