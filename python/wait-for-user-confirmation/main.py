import os
import shutil
from acontext import AcontextClient
from dotenv import load_dotenv
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

    # Create a learning space and trigger learning
    print_console.rule("Learning from Session")
    space = acontext_client.learning_spaces.create()
    acontext_client.learning_spaces.learn(space.id, session_id=session.id)
    print_console.print(f"Created learning space: {space.id}")

    # Wait for learning to complete
    print_console.print("Waiting for learning to complete...")
    result = acontext_client.learning_spaces.wait_for_learning(space.id, session_id=session.id)
    print_console.print(f"Learning status: {result.status}")

    # List learned skills
    skills = acontext_client.learning_spaces.list_skills(space.id)
    print_console.rule(f"Learned Skills ({len(skills)})")
    for skill in skills:
        print_console.print(f"  - {skill.name}: {skill.description}")
        print_console.print(f"    files: {[f.path for f in skill.file_index]}")

    # Download all skill files
    download_dir = "./skills_output"
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)

    print_console.print(f"\nDownloading skills to {download_dir}/")
    for skill in skills:
        resp = acontext_client.skills.download(skill_id=skill.id, path=f"{download_dir}/{skill.name}")
        print_console.print(f"  {resp.name} -> {resp.dir_path}")
        for f in resp.files:
            print_console.print(f"    {f}")


if __name__ == "__main__":
    main()
