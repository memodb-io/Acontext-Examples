import asyncio
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from acontext import AcontextClient
from time import sleep

load_dotenv()
acontext_client = AcontextClient(
    api_key=os.getenv("ACONTEXT_API_KEY", "sk-ac-your-root-api-bearer-token"),
    base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1"),
    timeout=60,
)

# Tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Returns weather info for the specified city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city to get weather for",
                    }
                },
                "required": ["city"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Book a flight.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_city": {
                        "type": "string",
                        "description": "The departure city",
                    },
                    "to_city": {
                        "type": "string",
                        "description": "The destination city",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the flight",
                    },
                },
                "required": ["from_city", "to_city", "date"],
                "additionalProperties": False,
            },
        },
    },
]


# Tool implementations
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"


def book_flight(from_city: str, to_city: str, date: str) -> str:
    """Book a flight."""
    # Dummy implementation - returns simulated booking results
    return f"Flight booked successfully for '{from_city}' to '{to_city}' on '{date}'"


def execute_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool by name with given arguments."""
    if tool_name == "get_weather":
        return get_weather(**tool_args)
    elif tool_name == "book_flight":
        return book_flight(**tool_args)
    else:
        return f"Unknown tool: {tool_name}"


def create_openai_client() -> OpenAI:
    """Create an OpenAI client."""
    base_url = os.getenv("OPENAI_BASE_URL", None)
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)


def append_message(message: dict, conversation: list[dict], session_id: str):
    """Append a message to conversation and send to Acontext."""
    conversation.append(message)
    acontext_client.sessions.store_message(session_id=session_id, blob=message)
    return conversation


def run_agent(client: OpenAI, conversation: list[dict]) -> tuple[str, list[dict]]:
    """Run the agent with the given conversation and return the response content and all new messages."""
    messages_to_send = [
        {"role": "system", "content": "You are a helpful assistant"}
    ] + conversation

    new_messages = []
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_to_send,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Convert message to dict format
        message_dict = {"role": message.role, "content": message.content}

        # Handle tool calls
        if message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        messages_to_send.append(message_dict)
        new_messages.append(message_dict)

        # If there are no tool calls, we're done
        if not message.tool_calls:
            break

        # Execute tool calls
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Execute the function
            function_result = execute_tool(function_name, function_args)

            # Add tool response to messages
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_result,
            }
            messages_to_send.append(tool_message)
            new_messages.append(tool_message)

    # Get the final assistant response
    final_content = message.content if message.content else ""
    return final_content, new_messages


async def session_1(session_id: str):
    client = create_openai_client()

    # Build conversation history using OpenAI message format
    # This format works with both OpenAI and Acontext
    conversation: list[dict] = []

    # First interaction - ask for trip plan
    print("\n=== First interaction: Planning trip ===")
    user_msg_1 = {
        "role": "user",
        "content": "I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan",
    }
    conversation = append_message(user_msg_1, conversation, session_id)

    response_content, new_messages = run_agent(client, conversation)
    print(f"\nAssistant: {response_content}")

    for msg in new_messages:
        conversation = append_message(msg, conversation, session_id)

    # Second interaction - check weather
    print("\n\n=== Second interaction: Checking weather ===")
    conversation = append_message(
        {"role": "user", "content": "The plan sounds good, check the weather there"},
        conversation,
        session_id,
    )

    response_content, new_messages = run_agent(client, conversation)
    print(f"\nAssistant: {response_content}")

    for msg in new_messages:
        conversation = append_message(msg, conversation, session_id)

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

    response_content, new_messages = run_agent(client, conversation)
    print(f"\nAssistant: {response_content}")

    for msg in new_messages:
        conversation = append_message(msg, conversation, session_id)

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
    client = create_openai_client()

    messages = acontext_client.sessions.get_messages(session_id)
    conversation: list[dict] = messages.items
    conversation.append(
        {"role": "user", "content": "Summarize the conversation so far"}
    )

    response_content, _ = run_agent(client, conversation)
    print(f"\nAssistant: {response_content}")


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
