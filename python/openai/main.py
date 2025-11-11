"""
Main entry point demonstrating OpenAI + Acontext integration.

This script shows how to:
1. Use OpenAI SDK to create chat completions
2. Send OpenAI messages to Acontext sessions
3. Retrieve tasks from Acontext
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from acontext import AcontextClient
import time
import itertools


def main():
    # Load environment variables
    load_dotenv()

    # Initialize clients
    openai_api_key = os.getenv("OPENAI_API_KEY")
    acontext_api_key = os.getenv("ACONTEXT_API_KEY")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    if not acontext_api_key:
        raise ValueError("ACONTEXT_API_KEY environment variable is required")

    openai_client = OpenAI(api_key=openai_api_key)
    
    with AcontextClient(api_key=acontext_api_key, base_url=acontext_base_url) as acontext_client:
        # Create a space and session
        print("Creating Acontext space and session...")
        space = acontext_client.spaces.create()
        space_id = space.id
        print(f"Created space: {space_id}")

        session = acontext_client.sessions.create(space_id=space_id)
        session_id = session.id
        print(f"Created session: {session_id}")

        # User message
        user_message = "I need to write a landing page of iPhone 15 pro max, give me a plan in steps"
        print(f"\nUser: {user_message}")

        # Use OpenAI to generate a response
        print("Calling OpenAI API...")
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        assistant_content = response.choices[0].message.content
        print(f"Assistant: {assistant_content}")

        # Send assistant message to Acontext in OpenAI format
        acontext_client.sessions.send_message(
            session_id,
            blob={"role": "assistant", "content": assistant_content},
            format="openai"
        )
        print("✓ Assistant message sent to Acontext")


        # Poll until the latest message's session_task_process_status is "success"
        for _ in itertools.count():
            messages = acontext_client.sessions.get_messages(
                session_id,
                format="acontext",
                time_desc=True
            )
            latest_status = messages.items[0]["session_task_process_status"]
            if latest_status == "success":
                break
            time.sleep(2)

        # Retrieve all tasks from Acontext
        print("\nRetrieving tasks from Acontext...")
        tasks = acontext_client.sessions.get_tasks(
            session_id,
        )
        print(f"Found {len(tasks.items)} tasks in Acontext")


if __name__ == "__main__":
    main()

