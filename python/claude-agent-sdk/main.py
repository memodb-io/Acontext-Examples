import asyncio
from acontext import AcontextAsyncClient, ClaudeAgentStorage
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient


async def main():
    acontext_client = AcontextAsyncClient(api_key="sk-ac-your-api-key")
    storage = ClaudeAgentStorage(client=acontext_client)

    options = ClaudeAgentOptions(
        extra_args={"replay-user-messages": None},  # include UserMessage in stream
    )
    async with ClaudeSDKClient(options=options) as claude_client:
        await claude_client.query("What is the capital of France?")
        async for message in claude_client.receive_response():
            await storage.save_message(message)


asyncio.run(main())
