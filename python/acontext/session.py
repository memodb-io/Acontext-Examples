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
    
    with AcontextClient(api_key=acontext_api_key, base_url=acontext_base_url) as acontext_client:
        # Create a space and session
        print("Creating Acontext space and session...")
        space = acontext_client.spaces.create()
        
        session = acontext_client.sessions.create(space_id=space.id)
        
        test_messages = [
            {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "I need to write a landing page of iPhone 15 pro max"
                    }
                ]
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure, my plan is below:\n1. Search for the latest news about iPhone 15 pro max\n2. Init Next.js project for the landing page\n3. Deploy the landing page to the website"
                    }
                ]
            },
            {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": "That sounds good. Let's first collect the message and report to me before any landing page coding."
                    }
                ]
            },
            {
                "role": "assistant",
                "parts": [
                    {
                        "type": "text",
                        "text": "Sure, I will first collect the message then report to you before any landing page coding."
                    }
                ]
            }
        ]
        
        print("\nUploading messages to session...")
        for i, message in enumerate(test_messages):
            acontext_client.sessions.send_message(
                session.id,
                blob={"role": message["role"], "parts": message["parts"]},
                format="acontext"
            )
            print(f"✓ Sent message {i}/{len(test_messages)}")
        
        print("Waiting for task processing to complete...")
        
        for _ in itertools.count():
            messages = acontext_client.sessions.get_messages(
                session.id,
                format="acontext",
                time_desc=True
            )
            latest_status = messages.items[0]["session_task_process_status"]
            if latest_status == "success":
                break
            time.sleep(2)

        # Retrieve all tasks from Acontext
        print("\nRetrieving tasks from Acontext...")
        tasks = acontext_client.sessions.get_tasks(session.id)
        print(f"✓ Found {len(tasks.items)} tasks in Acontext")
        
if __name__ == "__main__":
    main()
