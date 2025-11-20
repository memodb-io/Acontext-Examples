"""
Main entry point demonstrating Acontext.

This script shows how to:
1. create and get sessions, create messages
2. Retrieve tasks
"""

import os
from dotenv import load_dotenv
from acontext import AcontextClient
import time
import itertools


def main():
    # Load environment variables
    load_dotenv()

    # Initialize clients
    acontext_api_key = os.getenv("ACONTEXT_API_KEY")
    acontext_base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")

    if not acontext_api_key:
        raise ValueError("ACONTEXT_API_KEY environment variable is required")

    with AcontextClient(
        api_key=acontext_api_key, base_url=acontext_base_url
    ) as acontext_client:
        # Create a space and session
        space = acontext_client.spaces.create()

        session = acontext_client.sessions.create(space_id=space.id)

        messages = [
            {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "I need to write a landing page of iPhone 15 pro max",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure, my plan is below:\n1. Search for the latest news about iPhone 15 pro max\n2. Init Next.js project for the landing page\n3. Deploy the landing page to the website",
                    }
                ],
            },
            {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "That sounds good. Let's first collect the message and report to me before any landing page coding.",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure, I will first collect the message then report to you before any landing page coding.",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "I need to search the latest news about iPhone 15 pro max first",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "tool-call",
                        "text": "search_news",
                        "meta": {
                            "name": "search_news",
                            "arguments": {"query": "iPhone 15 pro max launching"},
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "tool-call",
                        "text": "search_news",
                        "meta": {
                            "name": "search_news",
                            "arguments": {"query": "iPhone 15 pro max price"},
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "tool-call",
                        "text": "search_news",
                        "meta": {
                            "name": "search_news",
                            "arguments": {
                                "query": "iPhone 15 pro max features specifications"
                            },
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Based on my search results, here's what I found about the iPhone 15 Pro Max:",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "## iPhone 15 Pro Max Key Information\n\n**Launch Details:**\n- Released in September 2023\n- Available in Natural Titanium, Blue Titanium, White Titanium, and Black Titanium\n\n**Key Features:**\n- 6.7-inch Super Retina XDR display\n- A17 Pro chip with 6-core GPU\n- Pro camera system with 48MP main camera\n- Action Button replacing the mute switch\n- USB-C connectivity\n- Titanium design\n\n**Pricing:**\n- Starting at $1,199 for 256GB\n- 512GB model at $1,399\n- 1TB model at $1,599\n\nThis information should be perfect for creating an engaging landing page. Should I proceed with initializing the Next.js project?",
                    }
                ],
            },
            {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "Great research! Yes, please proceed with the Next.js project setup.",
                    }
                ],
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "I'll now create the Next.js project for the iPhone 15 Pro Max landing page.",
                    }
                ],
            },
        ]

        for message in messages:
            acontext_client.sessions.send_message(
                session_id=session.id, blob=message, format="acontext"
            )

        acontext_client.sessions.flush(session.id)
        tasks_response = acontext_client.sessions.get_tasks(session.id)
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
    main()
