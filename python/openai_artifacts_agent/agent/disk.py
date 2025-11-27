from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import requests

from acontext import AcontextClient, FileUpload


class DiskManager:
    """Lazy Acontext disk client used by the async tools."""

    def __init__(self) -> None:
        self._client: AcontextClient | None = None
        self._default_disk_id: str | None = None

    def _ensure_client(self) -> AcontextClient:
        # Lazily construct the client so we only hit the API when needed.
        if self._client is None:
            api_key = os.getenv("ACONTEXT_API_KEY")
            if not api_key:
                raise RuntimeError("Please configure ACONTEXT_API_KEY in your environment.")
            base_url = os.getenv("ACONTEXT_BASE_URL", "http://localhost:8029/api/v1")
            self._client = AcontextClient(api_key=api_key, base_url=base_url)
        return self._client

    def _normalize_path(self, path: str | None) -> str:
        if not path:
            return "/"
        normalized = path if path.startswith("/") else f"/{path}"
        if not normalized.endswith("/"):
            normalized += "/"
        return normalized

    def _resolve_disk_id(self, disk_id: str | None) -> str:
        if disk_id:
            return disk_id
        if self._default_disk_id:
            return self._default_disk_id
        env_disk = os.getenv("ACONTEXT_DISK_ID")
        if env_disk:
            self._default_disk_id = env_disk
            return env_disk
        client = self._ensure_client()
        disk = client.disks.create()
        self._default_disk_id = disk.id
        return disk.id

    def write_file(
        self,
        *,
        disk_id: str | None,
        file_path: str | None,
        filename: str,
        content: str,
        encoding: str,
        meta: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        resolved_disk = self._resolve_disk_id(disk_id)
        normalized_path = self._normalize_path(file_path)
        payload = FileUpload(filename=filename, content=content.encode(encoding))
        artifact = client.disks.artifacts.upsert(
            resolved_disk,
            file=payload,
            file_path=normalized_path,
            meta=meta or {},
        )
        return {
            "disk_id": resolved_disk,
            "path": artifact.path,
            "filename": artifact.filename,
            "meta": artifact.meta,
        }

    def read_file(
        self,
        *,
        disk_id: str | None,
        file_path: str | None,
        filename: str,
        max_chars: int,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        resolved_disk = self._resolve_disk_id(disk_id)
        normalized_path = self._normalize_path(file_path)
        result = client.disks.artifacts.get(
            resolved_disk,
            file_path=normalized_path,
            filename=filename,
            with_content=True,
        )
        if not result.content:
            raise RuntimeError("Failed to read file: server did not return content.")
        raw = result.content.raw
        content_str = raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")
        preview = content_str[:max_chars]
        truncated = len(content_str) > len(preview)
        return {
            "disk_id": resolved_disk,
            "path": normalized_path,
            "filename": filename,
            "content_preview": preview,
            "truncated": truncated,
            "meta": result.artifact.meta,
        }

    def download_file(
        self,
        *,
        disk_id: str | None,
        file_path: str | None,
        filename: str,
        destination_path: str | None,
        expire_seconds: int,
        timeout: int,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        resolved_disk = self._resolve_disk_id(disk_id)
        normalized_path = self._normalize_path(file_path)
        result = client.disks.artifacts.get(
            resolved_disk,
            file_path=normalized_path,
            filename=filename,
            with_public_url=True,
            expire=expire_seconds,
        )
        if not result.public_url:
            raise RuntimeError("Download failed: temporary link unavailable.")
        target = Path(destination_path) if destination_path else Path.cwd() / "downloads" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(result.public_url, timeout=timeout)
        resp.raise_for_status()
        target.write_bytes(resp.content)
        return {
            "disk_id": resolved_disk,
            "path": normalized_path,
            "filename": filename,
            "local_path": str(target),
            "bytes": len(resp.content),
            "public_url": result.public_url,
        }


disk_manager = DiskManager()

