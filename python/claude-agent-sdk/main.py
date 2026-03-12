import asyncio
import os
import shutil

from dotenv import load_dotenv

load_dotenv()

from acontext import AcontextAsyncClient, ClaudeAgentStorage
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient


async def main():
    acontext_client = AcontextAsyncClient(api_key=os.environ["ACONTEXT_API_KEY"])
    storage = ClaudeAgentStorage(client=acontext_client)

    options = ClaudeAgentOptions(
        extra_args={"replay-user-messages": None},
    )
    async with ClaudeSDKClient(options=options) as claude_client:
        await claude_client.query("What is the capital of France?")
        async for message in claude_client.receive_response():
            await storage.save_message(message)

    # Get the session ID from storage
    session_id = storage.session_id
    print(f"Session ID: {session_id}")

    # Create a learning space and trigger learning
    space = await acontext_client.learning_spaces.create()
    await acontext_client.learning_spaces.learn(space.id, session_id=session_id)
    print(f"Created learning space: {space.id}")

    # Wait for learning to complete
    print("Waiting for learning to complete...")
    result = await acontext_client.learning_spaces.wait_for_learning(space.id, session_id=session_id)
    print(f"Learning status: {result.status}")

    # List learned skills
    skills = await acontext_client.learning_spaces.list_skills(space.id)
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
        resp = await acontext_client.skills.download(skill_id=skill.id, path=f"{download_dir}/{skill.name}")
        print(f"  {resp.name} -> {resp.dir_path}")
        for f in resp.files:
            print(f"    {f}")

    await acontext_client.close()


asyncio.run(main())
