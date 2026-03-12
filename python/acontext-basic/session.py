"""
Main entry point demonstrating Acontext.

This script shows how to:
1. create and get sessions, create messages
2. Learn from sessions and retrieve skills
"""

import os
import shutil
from dotenv import load_dotenv
from acontext import AcontextClient


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
        # Create a session
        session = acontext_client.sessions.create()

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
            acontext_client.sessions.store_message(
                session_id=session.id, blob=message, format="acontext"
            )

        # Create a learning space and trigger learning
        space = acontext_client.learning_spaces.create()
        acontext_client.learning_spaces.learn(space.id, session_id=session.id)
        print(f"\nCreated learning space: {space.id}")

        # Wait for learning to complete
        print("Waiting for learning to complete...")
        result = acontext_client.learning_spaces.wait_for_learning(space.id, session_id=session.id)
        print(f"Learning status: {result.status}")

        # List learned skills
        skills = acontext_client.learning_spaces.list_skills(space.id)
        print(f"\n=== Learned Skills ({len(skills)}) ===")
        for skill in skills:
            print(f"\n  - {skill.name}: {skill.description}")
            print(f"    files: {[f.path for f in skill.file_index]}")

        # Download all skill files
        download_dir = "./skills_output"
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)

        print(f"\nDownloading skills to {download_dir}/")
        for skill in skills:
            resp = acontext_client.skills.download(skill_id=skill.id, path=f"{download_dir}/{skill.name}")
            print(f"  {resp.name} -> {resp.dir_path}")
            for f in resp.files:
                print(f"    {f}")


if __name__ == "__main__":
    main()
