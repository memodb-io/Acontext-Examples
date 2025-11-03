"""
Main entry point demonstrating OpenAI + Acontext integration.

This script shows how to:
1. Use OpenAI SDK to create chat completions
2. Send OpenAI messages to Acontext sessions
3. Retrieve conversation history from Acontext
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from acontext import AcontextClient
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)


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
        user_message = "What is the capital of France?"
        print(f"\nUser: {user_message}")

        # Send user message to Acontext in OpenAI format
        user_msg = ChatCompletionUserMessageParam(role="user", content=user_message)
        acontext_client.sessions.send_message(
            session_id,
            blob=user_msg,
            format="openai"
        )
        print("✓ User message sent to Acontext")

        # Use OpenAI to generate a response
        print("Calling OpenAI API...")
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_message}]
        )
        assistant_content = response.choices[0].message.content
        print(f"Assistant: {assistant_content}")

        # Send assistant message to Acontext in OpenAI format
        assistant_msg = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=assistant_content
        )
        acontext_client.sessions.send_message(
            session_id,
            blob=assistant_msg,
            format="openai"
        )
        print("✓ Assistant message sent to Acontext")

        # Retrieve messages from Acontext
        print("\nRetrieving conversation history from Acontext...")
        messages = acontext_client.sessions.get_messages(
            session_id,
            format="openai",
            time_desc=True
        )
        print(f"Found {len(messages.messages)} messages in Acontext")
        
        print("\nConversation history:")
        for msg in messages.messages:
            role = msg.role
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"  {role}: {content}")

        print("\n✓ Integration complete!")


if __name__ == "__main__":
    main()

