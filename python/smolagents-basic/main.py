import inspect
import json
import os
import time
from functools import wraps
from typing import Any, List, Dict, Callable
from acontext import AcontextClient
from dotenv import load_dotenv
from smolagents import Tool, ToolCallingAgent, OpenAIModel
from smolagents.memory import TaskStep, ActionStep, FinalAnswerStep


load_dotenv()
client = AcontextClient(
    api_key=os.getenv("ACONTEXT_API_KEY", "sk-ac-your-root-api-bearer-token"),
    base_url=os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1"),
    timeout=60,
)


class ToolInvocationLogger:
    """Manages tool invocation logging for message reconstruction."""

    def __init__(self):
        self.invocations: List[Dict[str, Any]] = []

    def clear(self):
        """Clear all logged invocations."""
        self.invocations.clear()

    def log(self, tool_name: str, parameters: Dict[str, Any], result: Any):
        """Log a tool invocation."""
        try:
            structured_result = (
                json.loads(result) if isinstance(result, str) else {"result": result}
            )
        except (json.JSONDecodeError, TypeError):
            structured_result = {"message": str(result)}

        self.invocations.append(
            {
                "name": tool_name,
                "parameters": parameters,
                "structured_result": structured_result,
            }
        )

    def create_logger_decorator(self) -> Callable:
        """Create a decorator that logs tool invocations."""
        logger_instance = self  # Capture the logger instance in closure

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(tool_self, *args, **kwargs):
                tool_name = getattr(tool_self, "name", func.__name__)
                sig = inspect.signature(func)
                bound_args = sig.bind(tool_self, *args, **kwargs)
                bound_args.apply_defaults()
                parameters = {
                    k: v for k, v in bound_args.arguments.items() if k != "self"
                }

                result = func(tool_self, *args, **kwargs)
                logger_instance.log(tool_name, parameters, result)
                return result

            return wrapper

        return decorator


# Global logger instance
_logger = ToolInvocationLogger()
log_tool_invocation = _logger.create_logger_decorator()


class GetWeatherTool(Tool):
    name = "get_weather"
    description = "Returns weather info for the specified city."
    inputs = {
        "city": {"type": "string", "description": "The city to get weather for"},
    }
    output_type = "string"

    @log_tool_invocation
    def forward(self, city: str) -> str:
        message = f"The weather in {city} is sunny"
        return message


class BookFlightTool(Tool):
    name = "book_flight"
    description = "Book a flight."
    inputs = {
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
    }
    output_type = "string"

    @log_tool_invocation
    def forward(self, from_city: str, to_city: str, date: str) -> str:
        message = (
            f"Flight booked successfully for '{from_city}' "
            f"to '{to_city}' on '{date}'"
        )
        return message


def build_agent() -> ToolCallingAgent:
    model = OpenAIModel(
        model_id=os.getenv("SMOLAGENTS_MODEL_ID", "gpt-4.1"),
        api_key=os.environ["OPENAI_API_KEY"],
        api_base=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    tools = [GetWeatherTool(), BookFlightTool()]
    return ToolCallingAgent(
        model=model,
        tools=tools,
        max_steps=4,
        stream_outputs=False,
    )


def build_openai_messages(user_prompt: str, final_answer: str) -> List[Dict[str, Any]]:
    """
    Build OpenAI-format messages from user prompt, tool invocations, and final answer.

    Uses the NEW Tools API format (tool_calls):
    - Assistant message with tool_calls array
    - Tool responses with role='tool' and tool_call_id

    Format example:
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": None, "tool_calls": [...]},
        {"role": "tool", "tool_call_id": "...", "content": "..."},
        {"role": "assistant", "content": "..."}
    ]
    """
    messages: List[Dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    if not _logger.invocations:
        messages.append({"role": "assistant", "content": final_answer})
        return messages

    # Build tool calls and responses using NEW Tools API format
    tool_calls = []
    tool_responses = []

    for idx, invocation in enumerate(_logger.invocations, start=1):
        tool_call_id = f"call_{invocation['name']}_{idx}"
        # New format: tool_calls array with id, type, and function
        tool_calls.append(
            {
                "id": tool_call_id,
                "type": "function",
                "function": {
                    "name": invocation["name"],
                    "arguments": json.dumps(
                        invocation["parameters"], ensure_ascii=False
                    ),
                },
            }
        )
        # New format: tool response with role='tool' and tool_call_id
        tool_responses.append(
            {
                "role": "tool",  # ✅ New format uses 'tool', not 'function'
                "tool_call_id": tool_call_id,
                "content": json.dumps(
                    invocation["structured_result"], ensure_ascii=False
                ),
            }
        )

    # Assistant message with tool_calls (new format)
    messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
    # Tool responses (new format)
    messages.extend(tool_responses)
    # Final assistant response
    messages.append({"role": "assistant", "content": final_answer})

    return messages


def extract_messages_from_memory_steps(
    agent: ToolCallingAgent, previous_step_count: int = 0
) -> List[Dict[str, Any]]:
    """
    Extract OpenAI-format messages from agent.memory.steps.

    Args:
        agent: The agent with memory steps
        previous_step_count: Number of steps already processed (to only get new ones)

    Returns:
        List of OpenAI-format messages extracted from memory steps
    """
    messages: List[Dict[str, Any]] = []

    # Only process new steps (after previous_step_count)
    new_steps = agent.memory.steps[previous_step_count:]

    for step in new_steps:
        if isinstance(step, TaskStep):
            # TaskStep becomes a user message
            content = step.task
            if step.task_images:
                # Handle images if present
                msg_content = [{"type": "text", "text": content}]
                for img in step.task_images:
                    msg_content.append({"type": "image", "image": img})
                messages.append({"role": "user", "content": msg_content})
            else:
                messages.append({"role": "user", "content": content})

        elif isinstance(step, ActionStep):
            # ActionStep can contain:
            # 1. Assistant message with tool_calls (if tool_calls exist)
            # 2. Tool response messages (from observations)
            # 3. Assistant final answer (if model_output exists and no tool_calls)

            # Get tool_calls from step.tool_calls or model_output_message.tool_calls
            tool_calls_list = step.tool_calls
            if (
                not tool_calls_list
                and step.model_output_message
                and hasattr(step.model_output_message, "tool_calls")
            ):
                tool_calls_list = step.model_output_message.tool_calls

            # Check if there are tool calls
            if tool_calls_list and len(tool_calls_list) > 0:
                # Convert smolagents ToolCall to OpenAI format
                tool_calls = []
                for tc in tool_calls_list:
                    # Handle both ToolCall objects and dict format
                    if hasattr(tc, "id"):
                        # It's a ToolCall object
                        tc_id = tc.id
                        tc_name = tc.name
                        tc_args = tc.arguments
                    else:
                        # It's a dict
                        tc_id = tc.get("id", f"call_{len(tool_calls)}")
                        tc_name = tc.get("name", "unknown")
                        tc_args = tc.get("arguments", {})

                    # Format arguments
                    if isinstance(tc_args, dict):
                        args_str = json.dumps(tc_args, ensure_ascii=False)
                    elif isinstance(tc_args, str):
                        args_str = tc_args
                    else:
                        args_str = str(tc_args)

                    tool_calls.append(
                        {
                            "id": tc_id,
                            "type": "function",
                            "function": {
                                "name": tc_name,
                                "arguments": args_str,
                            },
                        }
                    )

                # Assistant message with tool_calls
                messages.append(
                    {"role": "assistant", "content": None, "tool_calls": tool_calls}
                )

                # Tool response messages
                if step.observations:
                    # Create tool responses for each tool call
                    # If multiple tool calls, split observations if possible, otherwise use same for all
                    observations_list = [step.observations] * len(tool_calls)

                    for idx, tc in enumerate(tool_calls):
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": (
                                    observations_list[idx]
                                    if idx < len(observations_list)
                                    else ""
                                ),
                            }
                        )

            # If there's a model output without tool calls, it's a final answer or assistant response
            elif step.model_output:
                # Only add if it's not empty and not just whitespace
                model_output_str = str(step.model_output).strip()
                if model_output_str:
                    messages.append({"role": "assistant", "content": model_output_str})

        elif isinstance(step, FinalAnswerStep):
            # FinalAnswerStep becomes assistant message
            messages.append({"role": "assistant", "content": str(step.output)})

    return messages


def run_agent_and_build_messages(
    agent: ToolCallingAgent, user_prompt: str, reset: bool = False
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Run agent and convert the execution to OpenAI message format.

    Uses agent's built-in memory management with reset=False to maintain conversation history.

    Args:
        agent: The agent to run
        user_prompt: The current user prompt
        reset: Whether to reset agent memory (default: False to maintain history)

    Returns:
        Tuple of (final_answer, messages) where messages are in OpenAI format
    """
    _logger.clear()

    # Store step count before running to extract only new messages
    previous_step_count = len(agent.memory.steps)

    # Run agent with reset parameter (False maintains conversation history)
    final_answer = agent.run(user_prompt, reset=reset)

    # Extract messages from memory steps (only new ones)
    messages = extract_messages_from_memory_steps(agent, previous_step_count)

    return final_answer, messages


def send_message(
    client: "AcontextClient", message: Dict[str, Any], session_id: str
) -> None:
    """Send a message to Acontext."""
    client.sessions.send_message(session_id=session_id, blob=message, format="openai")


def session_1(
    agent: ToolCallingAgent, client: "AcontextClient", session_id: str
) -> None:
    """First session: Run multiple interactions and save to Acontext."""
    all_messages = []  # Collect all messages, send at the end

    # First interaction - ask for trip plan (reset=True to start fresh)
    print("\n=== First interaction: Planning trip ===")
    user_msg_1_content = "my name is Elon! I'd like to have a 3-day trip in Finland. I like to see the nature. Give me the plan"
    final_answer, messages = run_agent_and_build_messages(
        agent, user_msg_1_content, reset=True
    )
    print(final_answer)
    all_messages.extend(messages)

    # Second interaction - check weather (reset=False to maintain history)
    print("\n=== Second interaction: Checking weather ===")
    user_msg_2_content = "The plan sounds good, check the weather there. And who am I?"
    final_answer, messages = run_agent_and_build_messages(
        agent, user_msg_2_content, reset=False
    )
    print(final_answer)
    all_messages.extend(messages)

    # Third interaction - book flight (reset=False to maintain history)
    print("\n=== Third interaction: Booking flight ===")
    user_msg_3_content = (
        "The weather is good, I am in Shanghai now, let's book the flight, "
        "you should just call the tool and don't ask me for more information. "
        "Remember, I only want the cheapest flight."
    )
    final_answer, messages = run_agent_and_build_messages(
        agent, user_msg_3_content, reset=False
    )
    print(final_answer)
    all_messages.extend(messages)

    # Fourth interaction - thank you (reset=False to maintain history)
    print("\n=== Fourth interaction: Thank you ===")
    user_msg_4_content = "cool, everything is done, thank you!"
    final_answer, messages = run_agent_and_build_messages(
        agent, user_msg_4_content, reset=False
    )
    print(final_answer)
    all_messages.extend(messages)

    # Send all messages to Acontext at once (like openai-agent-basic)
    print("\n=== Sending all messages to Acontext ===")
    print(all_messages)
    for msg in all_messages:
        send_message(client, msg, session_id)

    print(
        f"\nSaved {len(all_messages)} messages in conversation, waiting for tasks extraction..."
    )

    # Flush and get tasks
    client.sessions.flush(session_id)
    tasks_response = client.sessions.get_tasks(session_id)

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


def messages_to_string(messages) -> str:
    """
    Convert OpenAI-format messages to a string representation.

    Args:
        messages: Messages from Acontext (messages.items)

    Returns:
        String representation of the conversation
    """
    conversation_parts = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls")

        if role == "user":
            if isinstance(content, list):
                # Handle content array (may contain text and images)
                text_parts = [
                    item.get("text", "")
                    for item in content
                    if item.get("type") == "text"
                ]
                conversation_parts.append(f"User: {''.join(text_parts)}")
            else:
                conversation_parts.append(f"User: {content}")

        elif role == "assistant":
            if tool_calls:
                # Assistant called tools
                tool_info = []
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_info.append(
                        f"{func.get('name', 'unknown')}({func.get('arguments', '')})"
                    )
                conversation_parts.append(
                    f"Assistant: [Called tools: {', '.join(tool_info)}]"
                )

            if content:
                if isinstance(content, list):
                    text_parts = [
                        item.get("text", "")
                        for item in content
                        if item.get("type") == "text"
                    ]
                    content_str = "".join(text_parts)
                else:
                    content_str = content
                if content_str.strip():
                    conversation_parts.append(f"Assistant: {content_str}")

        elif role == "tool":
            tool_call_id = msg.get("tool_call_id", "")
            tool_content = msg.get("content", "")
            conversation_parts.append(f"Tool ({tool_call_id}): {tool_content}")

    return "\n".join(conversation_parts)


def session_2(
    agent: ToolCallingAgent, client: "AcontextClient", session_id: str
) -> None:
    """Second session: Get messages from Acontext and continue conversation."""
    messages = client.sessions.get_messages(session_id, format="openai")

    # Convert messages to string format (since smolagents agent.run() only accepts string)
    conversation_string = messages_to_string(messages.items)

    # Create user prompt that includes the conversation history and asks for summary
    user_prompt = f"""Here is the conversation history:

{conversation_string}

Please summarize the conversation so far."""

    final_answer, _ = run_agent_and_build_messages(agent, user_prompt, reset=False)
    print(f"\nAssistant: {final_answer}")


def main() -> None:

    space = client.spaces.create(configs={"name": "smolagents-basic-space"})
    space_id = space.id
    print(f"Created space: {space_id}")

    session = client.sessions.create(
        space_id=space_id,
        configs={"mode": "smolagents-toolcalling"},
    )
    session_id = session.id
    print(f"Created session: {session_id}")

    agent_session1 = build_agent()
    agent_session2 = build_agent()
    try:
        print("\n=== Session 1 ===")
        session_1(agent_session1, client, session_id)

        print("\n=== Session 2, get messages from Acontext and continue ===")
        session_2(agent_session2, client, session_id)

        print("\n=== Experiences from Acontext ===")
        print("Waiting for the agent learning", end="", flush=True)
        while True:
            status = client.sessions.get_learning_status(session_id)
            if status.not_space_digested_count == 0:
                break
            time.sleep(1)
            print(".", end="", flush=True)
        print("\n")
        print(
            client.spaces.experience_search(
                space_id=space_id, query="travel with flight", mode="fast"
            )
        )
    finally:
        client.close()


if __name__ == "__main__":
    main()
