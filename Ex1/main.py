"""
main.py
Entry point for the company chatbot.
Run:  python main.py
"""

import os
import httpx
from dotenv import load_dotenv

# Workaround for corporate proxy / missing root CA certificates
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"

from agent import build_agent


def main():
    load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider == "azure":
        if not os.getenv("AZURE_OPENAI_API_KEY"):
            print("ERROR: AZURE_OPENAI_API_KEY is not set. Please edit .env and add your key.")
            return
        if not os.getenv("AZURE_OPENAI_ENDPOINT"):
            print("ERROR: AZURE_OPENAI_ENDPOINT is not set. Please edit .env and add your endpoint.")
            return
    else:
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
