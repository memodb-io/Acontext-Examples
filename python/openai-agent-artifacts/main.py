"""Minimal async Acontext Artifact Agent using the OpenAI Python SDK."""
import asyncio
import os
from pathlib import Path
from acontext import AcontextClient
from dotenv import load_dotenv
from agent import AcontextArtifactAgent


async def main() -> None:
    env_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Please set OPENAI_API_KEY in the environment or .env file.")

    base_url = os.getenv("OPENAI_BASE_URL")
    
    # Create Acontext client and disk
    acontext_api_key = os.getenv("ACONTEXT_API_KEY")
    if not acontext_api_key:
        raise RuntimeError("Please set ACONTEXT_API_KEY in the environment or .env file.")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")
    client = AcontextClient(api_key=acontext_api_key, base_url=acontext_base_url)
    disk = client.disks.create()
    
    print(f"Created disk with ID: {disk.id}")
    
    user_query = (
        "Please create /notes/demo.txt with a short summary about your tools, "
        "then list the artifacts in /notes/ directory, "
        "read the file back to confirm it was written, "
        "and finally download the file locally to verify the download tool."
    )

    print("Starting agent execution...")
    print(f"Disk ID: {disk.id}")
    print(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
    print(f"Max Turns: 5")

    async with AcontextArtifactAgent(
        api_key=api_key,
        base_url=base_url,
        disk_id=disk.id,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_turn=5,
    ) as agent:
        result = await agent.run(user_query)
        print(f"Agent completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())

