import os
import sys
import json
from openai import OpenAI
from acontext import AcontextClient, FileUpload
from acontext.agent import SANDBOX_TOOLS

oai_client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
)

if len(sys.argv) < 2:
    print(
        "Usage: python create_skill_sandbox.py <path_to_zip_file> <model_name optional>"
    )
    exit()
ZIP_PATH = sys.argv[1]
MODEL_NAME = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1"

client = AcontextClient(
    # base_url="http://localhost:8029/api/v1",
    # api_key="sk-ac-your-root-api-bearer-token",
    api_key=os.getenv("ACONTEXT_API_KEY")
)

with open(ZIP_PATH, "rb") as f:
    skill_bin = f.read()
name = os.path.basename(ZIP_PATH)

r = client.skills.create(
    file=FileUpload(filename=name, content=skill_bin),
)
SN = r.name
sid = r.id


sandbox = client.sandboxes.create()
disk = client.disks.create()
try:
    # Create tool context with mounted skills
    ctx = SANDBOX_TOOLS.format_context(
        client=client,
        sandbox_id=sandbox.sandbox_id,
        disk_id=disk.id,
        mount_skills=[sid],
    )

    tools = SANDBOX_TOOLS.to_openai_tool_schema()
    system_prompt = f"""You are a helpful assistant with access to a secure sandbox environment.
You can execute bash commands, run Python scripts, and export files for the user.

{ctx.get_context_prompt()}"""

    messages = []
    max_iterations = 20

    print("\n--- Sandbox Ready ---")
    print("Type your requests (or 'quit' to exit, 'reset' to clear history)")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        if user_input.lower() == "reset":
            messages = []
            print("Conversation history cleared.")
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})
        print("\nAgent working...")

        # Agentic loop
        for iteration in range(max_iterations):
            print(f"\n[Iteration {iteration + 1}]")

            response = oai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=tools if tools else None,
                tool_choice="auto",
            )

            assistant_message = response.choices[0].message

            # Check if we're done (no tool calls)
            if not assistant_message.tool_calls:
                final_response = assistant_message.content or ""
                messages.append({"role": "assistant", "content": final_response})
                print(f"\nAgent: {final_response}")
                break

            # Process tool calls
            messages.append(assistant_message.model_dump())

            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  Tool: {tool_name}")
                print(f"  Args: {json.dumps(tool_args, indent=2)}")

                # Execute the tool
                try:
                    result = SANDBOX_TOOLS.execute_tool(
                        ctx=ctx,
                        tool_name=tool_name,
                        llm_arguments=tool_args,
                    )
                except Exception as e:
                    result = json.dumps({"error": str(e)})

                print(
                    f"  Result: {result[:200]}..."
                    if len(result) > 200
                    else f"  Result: {result}"
                )

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        else:
            print("Max iterations reached. Task may be incomplete.")

finally:
    client.sandboxes.kill(sandbox.sandbox_id)
