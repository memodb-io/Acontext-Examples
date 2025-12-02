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

    def write_file(
        self,
        *,
        disk_id: str,
        file_path: str | None,
        filename: str,
        content: str,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        normalized_path = self._normalize_path(file_path)
        payload = FileUpload(filename=filename, content=content.encode("utf-8"))
        artifact = client.disks.artifacts.upsert(
            disk_id,
            file=payload,
            file_path=normalized_path
        )
        return {
            "disk_id": disk_id,
            "path": artifact.path,
            "filename": artifact.filename,
        }

    def read_file(
        self,
        *,
        disk_id: str,
        file_path: str | None,
        filename: str,
        max_chars: int,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        normalized_path = self._normalize_path(file_path)
        result = client.disks.artifacts.get(
            disk_id,
            file_path=normalized_path,
            filename=filename,
            with_public_url=True,
            with_content=True,
        )
        if not result.content:
            raise RuntimeError("Failed to read file: server did not return content.")
        raw = result.content.raw
        content_str = raw if isinstance(raw, str) else raw.decode("utf-8", errors="replace")
        preview = content_str[:max_chars]
        truncated = len(content_str) > len(preview)
        return {
            "disk_id": disk_id,
            "path": normalized_path,
            "filename": filename,
            "content_preview": preview,
            "truncated": truncated,
        }

    def download_file(
        self,
        *,
        disk_id: str,
        file_path: str | None,
        filename: str,
        destination_path: str | None,
        expire_seconds: int,
        timeout: int,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        normalized_path = self._normalize_path(file_path)
        result = client.disks.artifacts.get(
            disk_id,
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
            "disk_id": disk_id,
            "path": normalized_path,
            "filename": filename,
            "local_path": str(target),
            "bytes": len(resp.content),
            "public_url": result.public_url,
        }

    def list_artifacts(
        self,
        *,
        disk_id: str,
        file_path: str | None,
    ) -> Dict[str, Any]:
        client = self._ensure_client()
        normalized_path = self._normalize_path(file_path) if file_path else None
        result = client.disks.artifacts.list(
            disk_id,
            path=normalized_path,
        )
        artifacts_list = [
            {
                "filename": artifact.filename,
                "path": artifact.path,
                "size_b": (
                    artifact.meta.get("__artifact_info__", {}).get("size")
                    if artifact.meta and isinstance(artifact.meta, dict)
                    else None
                ),
                "meta": artifact.meta,
            }
            for artifact in result.artifacts
        ]
        return {
            "disk_id": disk_id,
            "path": normalized_path or "/",
            "artifacts": artifacts_list,
            "directories": result.directories,
        }


disk_manager = DiskManager()

