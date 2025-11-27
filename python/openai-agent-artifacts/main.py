"""Minimal async React Agent using the OpenAI Python SDK."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from agent import react_agent


async def main() -> None:
    env_path = Path(__file__).with_name(".env")
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Please set OPENAI_API_KEY in the environment or .env file.")

    base_url = os.getenv("OPENAI_BASE_URL")
    user_query = (
        "Please create /notes/demo.txt with a short summary about your tools "
        "then read the file back to confirm it was written, "
        "and finally download the file locally to verify the download tool."
    )

    await react_agent(
        user_query=user_query,
        api_key=api_key,
        base_url=base_url,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        max_turn=5,
    )


if __name__ == "__main__":
    asyncio.run(main())

