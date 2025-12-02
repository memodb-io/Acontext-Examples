from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

from .disk import disk_manager

ToolFunc = Callable[..., Awaitable[str]]


@dataclass
class ToolDefinition:
    """Tool definition that combines schema and implementation."""

    name: str
    description: str
    parameters: Dict[str, Any]
    implementation_factory: Callable[[str], ToolFunc]  # Takes disk_id, returns async function

    def to_openai_schema(self) -> Dict[str, Any]:
        """Convert to OpenAI tool schema format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def create_implementation(self, disk_id: str) -> ToolFunc:
        """Create the actual implementation function with disk_id injected."""
        return self.implementation_factory(disk_id)


# Define tools with schema and implementation together
def _create_write_file_impl(disk_id: str) -> ToolFunc:
    """Create write_file implementation with disk_id injected."""
    async def write_file(filename: str, content: str, file_path: str | None = None) -> str:
        """Wrapper that automatically injects disk_id and uses default values for implementation details."""
        result = await asyncio.to_thread(
            disk_manager.write_file,
            disk_id=disk_id,
            file_path=file_path,
            filename=filename,
            content=content,
        )
        return json.dumps(result, ensure_ascii=False)
    return write_file


def _create_read_file_impl(disk_id: str) -> ToolFunc:
    """Create read_file implementation with disk_id injected."""
    async def read_file(filename: str, file_path: str | None = None) -> str:
        """Wrapper that automatically injects disk_id and uses default values for implementation details."""
        result = await asyncio.to_thread(
            disk_manager.read_file,
            disk_id=disk_id,
            file_path=file_path,
            filename=filename,
            max_chars=1200,
        )
        return json.dumps(result, ensure_ascii=False)
    return read_file


def _create_download_file_impl(disk_id: str) -> ToolFunc:
    """Create download_file implementation with disk_id injected."""
    async def download_file(filename: str, file_path: str | None = None) -> str:
        """Wrapper that automatically injects disk_id and uses default values for implementation details."""
        result = await asyncio.to_thread(
            disk_manager.download_file,
            disk_id=disk_id,
            file_path=file_path,
            filename=filename,
            destination_path=None,
            expire_seconds=3600,
            timeout=30,
        )
        return json.dumps(result, ensure_ascii=False)
    return download_file


def _create_list_artifacts_impl(disk_id: str) -> ToolFunc:
    """Create list_artifacts implementation with disk_id injected."""
    async def list_artifacts(file_path: str | None = None) -> str:
        """Wrapper that automatically injects disk_id and uses default values for implementation details."""
        result = await asyncio.to_thread(
            disk_manager.list_artifacts,
            disk_id=disk_id,
            file_path=file_path,
        )
        return json.dumps(result, ensure_ascii=False)
    return list_artifacts


TOOL_DEFINITIONS = [
    ToolDefinition(
        name="write_file",
        description="Write text content to a file in the file system. Creates the file if it doesn't exist, overwrites if it does.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Optional folder path to organize files, e.g. '/notes/' or '/documents/'. Defaults to root '/' if not specified.",
                },
                "filename": {"type": "string", "description": "Filename such as 'report.md' or 'demo.txt'."},
                "content": {"type": "string", "description": "Text content to write to the file."},
            },
            "required": ["filename", "content"],
        },
        implementation_factory=_create_write_file_impl,
    ),
    ToolDefinition(
        name="read_file",
        description="Read a text file from the file system and return its content.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Optional directory path where the file is located, e.g. '/notes/'. Defaults to root '/' if not specified.",
                },
                "filename": {"type": "string", "description": "Filename to read."},
            },
            "required": ["filename"],
        },
        implementation_factory=_create_read_file_impl,
    ),
    ToolDefinition(
        name="download_file",
        description="Download a file from the file system and save it locally to the ./downloads/ directory.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Optional directory path where the file is located, e.g. '/notes/'. Defaults to root '/' if not specified.",
                },
                "filename": {"type": "string", "description": "Filename to download."},
            },
            "required": ["filename"],
        },
        implementation_factory=_create_download_file_impl,
    ),
    ToolDefinition(
        name="list_artifacts",
        description="List all artifacts (files) and directories in a specified path on the disk.",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Optional directory path to list, e.g. '/todo/' or '/notes/'. Defaults to root '/' if not specified.",
                },
            },
            "required": [],
        },
        implementation_factory=_create_list_artifacts_impl,
    ),
]


def get_tools_schema() -> list[Dict[str, Any]]:
    """Get OpenAI tools schema list."""
    return [tool.to_openai_schema() for tool in TOOL_DEFINITIONS]


def create_tool_map(disk_id: str) -> Dict[str, ToolFunc]:
    """Create tool map with disk_id automatically injected."""
    return {tool.name: tool.create_implementation(disk_id) for tool in TOOL_DEFINITIONS}


__all__ = ["create_tool_map", "ToolDefinition", "TOOL_DEFINITIONS", "get_tools_schema"]

