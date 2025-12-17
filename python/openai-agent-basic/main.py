import asyncio
import os
from dotenv import load_dotenv
from time import sleep

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
        f"\nSaved {len(messages)} messages in conversation, waiting for tasks extraction..."
    )

    # Flush and get tasks
    acontext_client.sessions.flush(session_id)
    tasks_response = acontext_client.sessions.get_tasks(session_id)

    print("\n=== Extracted Tasks ===")
    for task in tasks_response.items:
        print(f"\nTask #{task.order}:")
        print(f"  ID: {task.id}")
        print(f"  Title: {task.data.task_description}")
        print(f"  Status: {task.status}")

        # Show progress updates if available
        if task.data.progresses:
            print(f"  Progress updates: {len(task.data.progresses)}")
            for progress in task.data.progresses:
                print(f"    - {progress}")

        # Show user preferences if available
        if task.data.user_preferences:
            print("  User preferences:")
            for pref in task.data.user_preferences:
                print(f"    - {pref}")


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
    space = acontext_client.spaces.create()
    space_id = space.id
    print(f"Created space: {space_id}")

    session = acontext_client.sessions.create(space_id=space_id)
    session_id = session.id
    print(f"Created session: {session_id}")

    print("\n=== Session 1 ===")
    await session_1(session_id)

    print("\n=== Session 2, get messages from Acontext and continue ===")
    await session_2(session_id)

    print("\n=== Experiences from Acontext ===")
    print("Waiting for the agent learning")
    while True:
        status = acontext_client.sessions.get_learning_status(session_id)
        if status.not_space_digested_count == 0:
            break
        sleep(1)
        print(".", end="", flush=True)
    print("\n")
    print(
        acontext_client.spaces.experience_search(
            space_id=space_id, query="travel with flight", mode="fast"
        )
    )

    # Close the client after all sessions are complete
    acontext_client.close()


if __name__ == "__main__":
    asyncio.run(main())
