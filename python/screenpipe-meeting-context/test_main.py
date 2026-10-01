import json
from types import SimpleNamespace
from unittest.mock import Mock

import acontext
import pytest
from acontext.errors import AcontextError

from main import MAX_BYTES, build_message, load_message, main

SESSION = "7c0896e0-2f5e-4f3c-8835-49123757ce7d"


@pytest.fixture
def meeting():
    return {
        "id": 42,
        "meeting_start": "2026-01-15T10:00:00Z",
        "meeting_end": "2026-01-15T10:30:00Z",
        "note": "CSV chosen; delivery unknown.",
    }


def test_only_note_and_provenance_are_selected(meeting):
    meeting.update(
        {"transcript": "private transcript", "attendees": "private attendee"}
    )
    result = build_message(meeting, "work-laptop")
    assert result["role"] == "user"
    assert "screenpipe:work-laptop:meeting:42" in result["content"]
    assert "CSV chosen; delivery unknown." in result["content"]
    assert "private" not in result["content"]
    assert "not instructions or verified execution results" in result["content"]


@pytest.mark.parametrize(
    "patch",
    [
        {"id": True},
        {"id": -1},
        {"id": "42"},
        {"note": None},
        {"note": " "},
        {"meeting_end": None},
        {"meeting_start": "invalid"},
        {"meeting_start": "2026-01-15T10:00:00"},
        {"meeting_end": "2026-01-15T09:00:00Z"},
        {"note": "a" * (64 * 1024 + 1)},
    ],
)
def test_rejects_invalid_or_unfinished_meetings(meeting, patch):
    meeting.update(patch)
    with pytest.raises((ValueError, TypeError)):
        build_message(meeting, "work-laptop")


def test_rejects_unsafe_device_label(meeting):
    with pytest.raises((ValueError, TypeError)):
        build_message(meeting, "device\nFake source")


@pytest.mark.parametrize(
    "content", [b"[]", b"invalid", b"\xff", b" " * (MAX_BYTES + 1)]
)
def test_rejects_invalid_export(tmp_path, content):
    path = tmp_path / "meeting.json"
    path.write_bytes(content)
    with pytest.raises((ValueError, TypeError)):
        load_message(path, "work-laptop")


def test_preview_never_constructs_client(tmp_path, meeting, monkeypatch, capsys):
    path = tmp_path / "meeting.json"
    path.write_text(json.dumps(meeting))
    client = Mock(side_effect=AssertionError("network client constructed"))
    monkeypatch.setattr(acontext, "AcontextClient", client)
    monkeypatch.delenv("ACONTEXT_API_KEY", raising=False)
    assert (
        main(["--meeting-json", str(path), "--device", "work", "--session-id", SESSION])
        == 0
    )
    assert json.loads(capsys.readouterr().out)["session_id"] == SESSION
    client.assert_not_called()


def test_send_requires_key(tmp_path, meeting, monkeypatch, capsys):
    path = tmp_path / "meeting.json"
    path.write_text(json.dumps(meeting))
    monkeypatch.delenv("ACONTEXT_API_KEY", raising=False)
    assert (
        main(
            [
                "--meeting-json",
                str(path),
                "--device",
                "work",
                "--session-id",
                SESSION,
                "--send",
            ]
        )
        == 1
    )
    assert "Set ACONTEXT_API_KEY" in capsys.readouterr().err


def test_explicit_send_and_credential_safe_failure(
    tmp_path, meeting, monkeypatch, capsys
):
    path = tmp_path / "meeting.json"
    path.write_text(json.dumps(meeting))
    store = Mock(return_value=SimpleNamespace(id="message-1"))
    client = Mock()
    client.__enter__ = Mock(
        return_value=SimpleNamespace(sessions=SimpleNamespace(store_message=store))
    )
    client.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(acontext, "AcontextClient", Mock(return_value=client))
    monkeypatch.setenv("ACONTEXT_API_KEY", "synthetic-test-key")
    args = [
        "--meeting-json",
        str(path),
        "--device",
        "work",
        "--session-id",
        SESSION,
        "--send",
    ]
    assert main(args) == 0
    store.assert_called_once_with(
        SESSION, blob=build_message(meeting, "work"), format="openai"
    )
    assert json.loads(capsys.readouterr().out)["message_id"] == "message-1"
    store.side_effect = AcontextError("synthetic-test-key " + meeting["note"])
    assert main(args) == 1
    output = capsys.readouterr()
    assert "synthetic-test-key" not in output.err
    assert meeting["note"] not in output.err
    assert "Check the session before retrying" in output.err


def test_real_sdk_serializes_selected_note(tmp_path, meeting, monkeypatch, capsys):
    import httpx

    path = tmp_path / "meeting.json"
    path.write_text(json.dumps(meeting))
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": {
                    "id": "message-1",
                    "session_id": SESSION,
                    "role": "user",
                    "meta": {},
                    "parts": [],
                    "session_task_process_status": "pending",
                    "created_at": "2026-01-15T10:30:00Z",
                    "updated_at": "2026-01-15T10:30:00Z",
                }
            },
        )

    real_client = acontext.AcontextClient
    monkeypatch.setattr(
        acontext,
        "AcontextClient",
        lambda api_key: real_client(
            api_key=api_key,
            base_url="https://acontext.example.test/api/v1",
            client=httpx.Client(transport=httpx.MockTransport(respond)),
        ),
    )
    monkeypatch.setenv("ACONTEXT_API_KEY", "synthetic-test-key")
    assert (
        main(
            [
                "--meeting-json",
                str(path),
                "--device",
                "work",
                "--session-id",
                SESSION,
                "--send",
            ]
        )
        == 0
    )
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert request.url.path == f"/api/v1/session/{SESSION}/messages"
    assert request.headers["Authorization"] == "Bearer synthetic-test-key"
    assert json.loads(request.content) == {
        "format": "openai",
        "blob": build_message(meeting, "work"),
    }
    assert json.loads(capsys.readouterr().out)["message_id"] == "message-1"
