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
    space = acontext_client.spaces.create()
    session = acontext_client.sessions.create(space_id=space.id)
    for m in messages:
        acontext_client.sessions.send_message(session_id=session.id, blob=m)
        print_console.print(f"[bold blue]{m['role']}[/bold blue]: {m['content']}")
    print_console.rule("Wait for Task Agent")
    acontext_client.sessions.flush(session.id)

    print_console.print(
        "[bold green]Waiting for the agent learning[/bold green] ", end=""
    )
    while True:
        status = acontext_client.sessions.get_learning_status(session.id)
        if status.not_space_digested_count == 0:
            break
        sleep(0.5)
        print_console.print(".", end="")
    print_console.print()

    unconfirmed_experiences = acontext_client.spaces.get_unconfirmed_experiences(
        space_id=space.id,
    )
    if not unconfirmed_experiences.items:
        print_console.print(
            "[bold green]No new experiences, maybe you should adjust the mock messages or just try again[/bold green]"
        )
        return

    for m in unconfirmed_experiences.items:
        print_console.rule("New Experience")
        print_console.print(m.experience_data)
        approve = (
            print_console.input("Do you approve this experience? (y/n): ")
            .lower()
            .strip()
        )
        if approve in ["y", "n"]:
            r = acontext_client.spaces.confirm_experience(
                space_id=space.id, experience_id=m.id, save=(approve == "y")
            )
            if r is None:
                print_console.print("[bold red]Rejected this experience[/bold red]")
            else:
                print_console.print(
                    f"[bold green]Approved this experience: {r.experience_data['data']['use_when']}[/bold green]"
                )
        else:
            raise ValueError("Invalid input")


if __name__ == "__main__":
    main()
