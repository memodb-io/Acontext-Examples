from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict

from .disk import disk_manager

ToolFunc = Callable[..., Awaitable[str]]


tools = [
    {
        "type": "function",
        "function": {
            "name": "write_disk_file",
            "description": "Write text content to (or overwrite) a file on Acontext Disk; creates a disk if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "disk_id": {"type": "string", "description": "Optional target disk ID; defaults to the cached or auto-created disk."},
                    "file_path": {"type": "string", "description": "Folder path, e.g. /notes/, automatically normalized with leading/trailing /."},
                    "filename": {"type": "string", "description": "Filename such as report.md."},
                    "content": {"type": "string", "description": "Text content to write."},
                    "encoding": {"type": "string", "description": "Encoding, defaults to utf-8."},
                    "meta": {
                        "type": "object",
                        "description": "Optional metadata stored in the artifact meta.",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_disk_file",
            "description": "Read a text file from Disk and return a preview snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "disk_id": {"type": "string", "description": "Optional disk ID."},
                    "file_path": {"type": "string", "description": "Directory path containing the file."},
                    "filename": {"type": "string", "description": "Filename."},
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum number of characters to return, defaults to 1200.",
                        "minimum": 1,
                        "maximum": 10000,
                    },
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "download_disk_file",
            "description": "Generate a temporary download link and save the file locally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "disk_id": {"type": "string", "description": "Optional disk ID."},
                    "file_path": {"type": "string", "description": "Directory path containing the file."},
                    "filename": {"type": "string", "description": "Filename."},
                    "destination_path": {
                        "type": "string",
                        "description": "Full local path to save the file; defaults to ./downloads/filename.",
                    },
                    "expire_seconds": {
                        "type": "integer",
                        "description": "Expiration time for the temporary link (seconds), defaults to 3600.",
                        "minimum": 60,
                        "maximum": 86400,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "HTTP timeout for the download request (seconds), defaults to 30.",
                        "minimum": 5,
                        "maximum": 120,
                    },
                },
                "required": ["filename"],
            },
        },
    },
]


async def write_disk_file(
    filename: str,
    content: str,
    disk_id: str | None = None,
    file_path: str | None = None,
    encoding: str = "utf-8",
    meta: Dict[str, Any] | None = None,
) -> str:
    result = await asyncio.to_thread(
        disk_manager.write_file,
        disk_id=disk_id,
        file_path=file_path,
        filename=filename,
        content=content,
        encoding=encoding,
        meta=meta,
    )
    return json.dumps(result, ensure_ascii=False)


async def read_disk_file(
    filename: str,
    disk_id: str | None = None,
    file_path: str | None = None,
    max_chars: int = 1200,
) -> str:
    result = await asyncio.to_thread(
        disk_manager.read_file,
        disk_id=disk_id,
        file_path=file_path,
        filename=filename,
        max_chars=max_chars,
    )
    return json.dumps(result, ensure_ascii=False)


async def download_disk_file(
    filename: str,
    disk_id: str | None = None,
    file_path: str | None = None,
    destination_path: str | None = None,
    expire_seconds: int = 3600,
    timeout: int = 30,
) -> str:
    result = await asyncio.to_thread(
        disk_manager.download_file,
        disk_id=disk_id,
        file_path=file_path,
        filename=filename,
        destination_path=destination_path,
        expire_seconds=expire_seconds,
        timeout=timeout,
    )
    return json.dumps(result, ensure_ascii=False)


tool_map: Dict[str, ToolFunc] = {
    "write_disk_file": write_disk_file,
    "read_disk_file": read_disk_file,
    "download_disk_file": download_disk_file,
}


__all__ = ["tools", "tool_map"]

