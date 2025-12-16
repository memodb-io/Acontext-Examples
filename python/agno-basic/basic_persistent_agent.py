import asyncio
import os
from dotenv import load_dotenv
from rich import print
from agno.agent import Agent, RunOutput
from agno.models.openai import OpenAIChat
from agno.tools import tool
from acontext import AcontextClient
from time import sleep

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
    acontext_client.sessions.send_message(session_id=session_id, blob=message)
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
        f"Saved {len(conversation)} messages in conversation, waiting for tasks extraction..."
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
    agent = create_agno_agent()

    messages = acontext_client.sessions.get_messages(session_id)
    conversation: list[dict] = messages.items
    conversation.append(
        {"role": "user", "content": "Summarize the conversation so far"}
    )
    response: RunOutput = agent.run(conversation)
    print(f"\nAssistant: {response.content}")


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
