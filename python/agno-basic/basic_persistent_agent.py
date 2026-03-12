import asyncio
import os
import shutil
from dotenv import load_dotenv
from rich import print
from agno.agent import Agent, RunOutput
from agno.models.openai import OpenAIChat
from agno.tools import tool
from acontext import AcontextClient

load_dotenv()
acontext_client = AcontextClient(
    api_key=os.getenv("ACONTEXT_API_KEY", "sk-ac-your-root-api-bearer-token"),
    base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1"),
    timeout=60,
)


@tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"


@tool
def book_flight(from_city: str, to_city: str, date: str) -> str:
    """Book a flight."""
    # Dummy implementation - returns simulated booking results
    return f"Flight booked successfully for '{from_city}' to '{to_city}' on '{date}'"


def create_agno_agent() -> Agent:
    """Create an agno agent with tools."""
    return Agent(
        name="Assistant",
        model=OpenAIChat(id="gpt-4.1", base_url=os.getenv("OPENAI_BASE_URL", None)),
        instructions="You are a helpful assistant",
        tools=[get_weather, book_flight],
        markdown=True,
        # debug_mode=True,  # Enable debug mode to see tool calls and execution details
    )


def append_messages(
    messages: list[dict], conversation: list[dict], session_id: str
) -> list[dict]:
    messages = messages[1:]  # exclude sys prompt
    new_messages = messages[len(conversation) :]  # exclude already messages
    for m in new_messages:
        conversation = append_message(m, conversation, session_id)
    return conversation


def append_message(message: dict, conversation: list[dict], session_id: str):
    conversation.append(message)
    acontext_client.sessions.store_message(session_id=session_id, blob=message)
    return conversation


async def session_1(session_id: str):

    agent = create_agno_agent()

    # Build conversation history using OpenAI message format
    # This format works with both agno and acontext
    conversation: list[dict] = []

    # First interaction - ask for trip plan
    print("\n=== First interaction: Planning trip ===")
    user_msg_1 = {
        "role": "user",
        "content": "I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan",
    }
    conversation = append_message(user_msg_1, conversation, session_id)

    response1: RunOutput = agent.run(conversation)
    print(f"\nAssistant: {response1.content}")
    new_messages = [m.to_dict() for m in response1.messages]

    conversation = append_messages(
        new_messages,
        conversation,
        session_id,
    )

    # Second interaction - check weather
    print("\n\n=== Second interaction: Checking weather ===")
    conversation = append_message(
        {"role": "user", "content": "The plan sounds good, check the weather there"},
        conversation,
        session_id,
    )

    response2: RunOutput = agent.run(conversation)
    print(f"\nAssistant: {response2.content}")

    new_messages = [m.to_dict() for m in response2.messages]

    conversation = append_messages(
        new_messages,
        conversation,
        session_id,
    )

    # Third interaction - book flight
    print("\n\n=== Third interaction: Booking flight ===")
    conversation = append_message(
        {
            "role": "user",
            "content": "The weather is good, I am in Shanghai now, let's book the flight, you should just call the tool and don't ask me for more information. Remember, I only want the cheapest flight.",
        },
        conversation,
        session_id,
    )

    response3: RunOutput = agent.run(conversation)
    print(f"\nAssistant: {response3.content}")

    new_messages = [m.to_dict() for m in response3.messages]

    conversation = append_messages(
        new_messages,
        conversation,
        session_id,
    )

    append_message(
        {
            "role": "user",
            "content": "cool, everything is done, thank you!",
        },
        conversation,
        session_id,
    )

    print(
        f"Saved {len(conversation)} messages in conversation, triggering learning..."
    )

    # Create a learning space and trigger learning
    space = acontext_client.learning_spaces.create()
    acontext_client.learning_spaces.learn(space.id, session_id=session_id)
    print(f"\nCreated learning space: {space.id}")

    # Wait for learning to complete
    print("Waiting for learning to complete...")
    result = acontext_client.learning_spaces.wait_for_learning(space.id, session_id=session_id)
    print(f"Learning status: {result.status}")

    # List learned skills
    skills = acontext_client.learning_spaces.list_skills(space.id)
    print(f"\n=== Learned Skills ({len(skills)}) ===")
    for skill in skills:
        print(f"\n  - {skill.name}: {skill.description}")
        print(f"    files: {[f.path for f in skill.file_index]}")

    # Download all skill files
    download_dir = "./skills_output"
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)

    print(f"\nDownloading skills to {download_dir}/")
    for skill in skills:
        resp = acontext_client.skills.download(skill_id=skill.id, path=f"{download_dir}/{skill.name}")
        print(f"  {resp.name} -> {resp.dir_path}")
        for f in resp.files:
            print(f"    {f}")


async def session_2(session_id: str):
    agent = create_agno_agent()

    messages = acontext_client.sessions.get_messages(session_id)
    conversation: list[dict] = messages.items
    conversation.append(
        {"role": "user", "content": "Summarize the conversation so far"}
    )
    response: RunOutput = agent.run(conversation)
    print(f"\nAssistant: {response.content}")


async def main():
    session = acontext_client.sessions.create()
    session_id = session.id
    print(f"Created session: {session_id}")

    print("\n=== Session 1 ===")
    await session_1(session_id)

    print("\n=== Session 2, get messages from Acontext and continue ===")
    await session_2(session_id)


    # Close the client after all sessions are complete
    acontext_client.close()


if __name__ == "__main__":
    asyncio.run(main())
