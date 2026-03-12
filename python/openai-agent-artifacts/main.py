"""Minimal async Acontext Artifact Agent using the OpenAI Python SDK."""
import asyncio
import os
import shutil
from pathlib import Path
from acontext import AcontextClient
from acontext.agent.disk import DISK_TOOLS
from dotenv import load_dotenv
from agent import AcontextArtifactAgent


async def main() -> None:
    env_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Please set OPENAI_API_KEY in the environment or .env file.")

    base_url = os.getenv("OPENAI_BASE_URL")
    print(base_url)
    print(api_key)

    # Create Acontext client and disk
    acontext_api_key = os.getenv("ACONTEXT_API_KEY")
    if not acontext_api_key:
        raise RuntimeError("Please set ACONTEXT_API_KEY in the environment or .env file.")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")
    client = AcontextClient(api_key=acontext_api_key, base_url=acontext_base_url)
    disk = client.disks.create()

    # Create tool context using DISK_TOOLS
    ctx = DISK_TOOLS.format_context(client, disk.id)

    print(f"Created disk with ID: {disk.id}")

    # Create a session to store the conversation
    session = client.sessions.create()
    print(f"Created session: {session.id}")

    user_query = (
        "Please create /notes/demo.txt with a short summary about your tools, "
        "then list the artifacts in /notes/ directory, "
        "read the file back to confirm it was written, "
        "and finally use replace_string to replace a word in the file."
    )

    # Store user message
    client.sessions.store_message(session_id=session.id, blob={"role": "user", "content": user_query})

    print("Starting agent execution...")
    print(f"Disk ID: {disk.id}")
    print(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"Max Turns: 5")

    async with AcontextArtifactAgent(
        api_key=api_key,
        base_url=base_url,
        tool_context=ctx,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_turn=5,
    ) as agent:
        result = await agent.run(user_query)
        print("Agent completed successfully!")

    # Store assistant response
    client.sessions.store_message(session_id=session.id, blob={"role": "assistant", "content": "Agent completed the disk operations successfully."})

    # Create a learning space and trigger learning
    space = client.learning_spaces.create()
    client.learning_spaces.learn(space.id, session_id=session.id)
    print(f"\nCreated learning space: {space.id}")

    # Wait for learning to complete
    print("Waiting for learning to complete...")
    learn_result = client.learning_spaces.wait_for_learning(space.id, session_id=session.id)
    print(f"Learning status: {learn_result.status}")

    # List learned skills
    skills = client.learning_spaces.list_skills(space.id)
    print(f"\n=== Learned Skills ({len(skills)}) ===")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")
        print(f"    files: {[f.path for f in skill.file_index]}")

    # Download all skill files
    download_dir = "./skills_output"
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)

    print(f"\nDownloading skills to {download_dir}/")
    for skill in skills:
        resp = client.skills.download(skill_id=skill.id, path=f"{download_dir}/{skill.name}")
        print(f"  {resp.name} -> {resp.dir_path}")
        for f in resp.files:
            print(f"    {f}")


if __name__ == "__main__":
    asyncio.run(main())

