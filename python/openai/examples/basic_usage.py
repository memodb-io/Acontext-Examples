"""
Advanced example demonstrating OpenAI + Acontext integration with multi-turn conversations.

This example shows:
1. Creating a conversation loop with OpenAI
2. Maintaining conversation history in Acontext
3. Retrieving and using conversation context
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from acontext import AcontextClient
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)


def create_conversation(openai_client: OpenAI, acontext_client: AcontextClient, 
                       session_id: str, user_input: str, conversation_history: list):
    """
    Create a conversation turn using OpenAI and store it in Acontext.
    
    Args:
        openai_client: OpenAI client instance
        acontext_client: Acontext client instance
        session_id: Acontext session ID
        user_input: User's message
        conversation_history: List of previous messages for OpenAI context
        
    Returns:
        Assistant's response content
    """
    # Send user message to Acontext
    user_msg = ChatCompletionUserMessageParam(role="user", content=user_input)
    acontext_client.sessions.send_message(
        session_id,
        blob=user_msg,
        format="openai"
    )
    print(f"  [User] {user_input}")

    # Add user message to conversation history
    conversation_history.append({"role": "user", "content": user_input})

    # Call OpenAI API with full conversation history
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=conversation_history
    )
    assistant_content = response.choices[0].message.content

    # Send assistant message to Acontext
    assistant_msg = ChatCompletionAssistantMessageParam(
        role="assistant",
        content=assistant_content
    )
    acontext_client.sessions.send_message(
        session_id,
        blob=assistant_msg,
        format="openai"
    )
    print(f"  [Assistant] {assistant_content}")

    # Add assistant message to conversation history
    conversation_history.append({"role": "assistant", "content": assistant_content})

    return assistant_content


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
        print("Setting up Acontext space and session...")
        space = acontext_client.spaces.create()
        session = acontext_client.sessions.create(space_id=space.id)
        session_id = session.id
        print(f"Created session: {session_id}\n")

        # Initialize conversation history
        conversation_history = []

        # Example conversation turns
        print("=== Starting Conversation ===\n")
        
        # First turn
        create_conversation(
            openai_client,
            acontext_client,
            session_id,
            "What is Python?",
            conversation_history
        )
        print()

        # Second turn (with context from previous messages)
        create_conversation(
            openai_client,
            acontext_client,
            session_id,
            "Can you give me a simple example?",
            conversation_history
        )
        print()

        # Third turn
        create_conversation(
            openai_client,
            acontext_client,
            session_id,
            "How do I install Python packages?",
            conversation_history
        )
        print()

        # Retrieve all messages from Acontext
        print("=== Retrieving from Acontext ===\n")
        messages = acontext_client.sessions.get_messages(
            session_id,
            format="openai",
            time_desc=False  # Get in chronological order
        )
        
        print(f"Total messages stored in Acontext: {len(messages.messages)}")
        print("\nFull conversation history:")
        for i, msg in enumerate(messages.messages, 1):
            role = msg.role
            content = msg.content if hasattr(msg, 'content') else str(msg)
            print(f"{i}. [{role.upper()}] {content}")

        print("\n✓ Multi-turn conversation example complete!")


if __name__ == "__main__":
    main()

