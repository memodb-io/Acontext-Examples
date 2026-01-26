from acontext import AcontextClient
from dotenv import load_dotenv
import os
from time import sleep
from rich.console import Console

load_dotenv()

acontext_client = AcontextClient(
    api_key=os.getenv("ACONTEXT_API_KEY", "sk-ac-your-root-api-bearer-token"),
    base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1"),
)
print_console = Console()


messages = [
    {
        "role": "user",
        "content": "I want to book a flight to Tokyo. Please help me to book the flight.",
    },
    {
        "role": "assistant",
        "content": "My task is to book the flight to Tokyo. I will start now.",
    },
    {
        "role": "assistant",
        "content": "I  have searched the flights",
    },
    {
        "role": "assistant",
        "content": "Done, I have selected the flight",
    },
    {
        "role": "user",
        "content": "You must remember: I only want the cheapest flight",
    },
    {
        "role": "assistant",
        "content": "Done, I have booked the flight",
    },
    {
        "role": "user",
        "content": "Yes, great job!",
    },
]


def main():
    print_console.rule("Sending Messages")
    session = acontext_client.sessions.create()
    for m in messages:
        acontext_client.sessions.store_message(session_id=session.id, blob=m)
        print_console.print(f"[bold blue]{m['role']}[/bold blue]: {m['content']}")
    print_console.rule("Wait for Task Agent")
    acontext_client.sessions.flush(session.id)


if __name__ == "__main__":
    main()
