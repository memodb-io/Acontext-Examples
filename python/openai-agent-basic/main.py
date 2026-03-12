import asyncio
import os
import shutil
from dotenv import load_dotenv

from agents import (
    Agent,
    Runner,
    ModelSettings,
    AsyncOpenAI,
    function_tool,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
from agents.models.chatcmpl_converter import Converter
from acontext import AcontextClient
from helper import message_to_input_items

load_dotenv()
acontext_client = AcontextClient(
    api_key=os.getenv("ACONTEXT_API_KEY", "sk-ac-your-root-api-bearer-token"),
    base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1"),
    timeout=60,
)


@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"


@function_tool
def book_flight(from_city: str, to_city: str, date: str) -> str:
    """Book a flight."""
    # Dummy implementation - returns simulated booking results
    return f"Flight booked successfully for '{from_city}' to '{to_city}' on '{date}'"


def create_agent():
    """Create an agent with the specified configuration."""
    set_tracing_disabled(disabled=True)
    return Agent(
        name="Assistant",
        instructions="You are a helpful assistant",
        model=OpenAIChatCompletionsModel(
            model="gpt-4o-mini",
            openai_client=AsyncOpenAI(),
        ),
        model_settings=ModelSettings(tool_choice="auto"),
        tools=[get_weather, book_flight],
    )


def store_message(message, session_id: str):
    """Store a message to Acontext."""
    acontext_client.sessions.store_message(session_id=session_id, blob=message, format="openai")




async def session_1(session_id: str):
    agent = create_agent()

    # First interaction - ask for trip plan
    print("\n=== First interaction: Planning trip ===")
    user_msg_1_content = "I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan"

    result = await Runner.run(agent, user_msg_1_content)

    # Second interaction - check weather
    print("\n=== Second interaction: Checking weather ===")
    user_msg_2 = {
        "role": "user",
        "content": "The plan sounds good, check the weather there",
    }
    new_input = result.to_input_list() + [user_msg_2]
    result = await Runner.run(agent, new_input)

    # Third interaction - book flight
    print("\n\n=== Third interaction: Booking flight ===")
    user_msg_3 = {
        "role": "user",
        "content": "The weather is good, I am in Shanghai now, let's book the flight, you should just call the tool and don't ask me for more information. Remember, I only want the cheapest flight.",
    }
    new_input = result.to_input_list() + [user_msg_3]
    result = await Runner.run(agent, new_input)

    # Fourth interaction - thank you
    user_msg_4 = {
        "role": "user",
        "content": "cool, everything is done, thank you!",
    }
    new_input = result.to_input_list() + [user_msg_4]
    result = await Runner.run(agent, new_input)

    messages = Converter.items_to_messages(result.to_input_list())
    for msg in messages:
        store_message(msg, session_id)

    print(
        f"\nSaved {len(messages)} messages in conversation, triggering learning..."
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
    agent = create_agent()

    messages = acontext_client.sessions.get_messages(session_id, format="openai")

    conversation = []

    for msg in messages.items:
        items = message_to_input_items(msg)
        conversation.extend(items)

    conversation.append(
        {"role": "user", "content": "Summarize the conversation so far"}
    )

    result = await Runner.run(agent, conversation)

    print(f"\nAssistant: {result.final_output}")


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
