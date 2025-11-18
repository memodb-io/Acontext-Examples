import asyncio

from agents import Agent, Runner, ModelSettings, AsyncOpenAI, function_tool, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.models.chatcmpl_converter import Converter

import os
from dotenv import load_dotenv
from acontext import AcontextClient


@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

async def main():
    load_dotenv()
    set_tracing_disabled(disabled=True)

    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant ",
        model=OpenAIChatCompletionsModel(
            model="gpt-4.1",
            openai_client=AsyncOpenAI(),
        ),
        model_settings=ModelSettings(tool_choice="auto"),
        tools=[get_weather],
    )

    result = await Runner.run(agent, "What city is the Golden Gate Bridge in? and What is the weather there?")
    new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
    result = await Runner.run(agent, new_input)
    messages = Converter.items_to_messages(result.to_input_list())

    acontext_client = AcontextClient(
        api_key=os.getenv("ACONTEXT_API_KEY"), base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")
    )

    space = acontext_client.spaces.create()
    space_id = space.id

    session = acontext_client.sessions.create(space_id=space_id)
    session_id = session.id
    for msg in messages:
        acontext_client.sessions.send_message(
            session_id=session_id, blob=msg, format="openai"
        )

    acontext_client.sessions.flush(session_id)
    tasks_response = acontext_client.sessions.get_tasks(session_id)
    for task in tasks_response.items:
        print(f"\nTask #{task.order}:")
        print(f"  ID: {task.id}")
        print(f"  Title: {task.data['task_description']}")
        print(f"  Status: {task.status}")

        # Show progress updates if available
        if "progresses" in task.data:
            print(f"  Progress updates: {len(task.data['progresses'])}")
            for progress in task.data["progresses"]:
                print(f"    - {progress}")

        # Show user preferences if available
        if "user_preferences" in task.data:
            print("  User preferences:")
            for pref in task.data["user_preferences"]:
                print(f"    - {pref}")


if __name__ == "__main__":
    asyncio.run(main())