# Screenpipe meeting context for Acontext

Add one reviewed [Screenpipe](https://github.com/screenpipe/screenpipe) meeting note
to an existing Acontext session. The default command previews the exact message
locally. `--send` stores it using the Acontext Python SDK.

This example supplies historical context to an agent session. It does not claim
to reconstruct tool executions or automatically produce a successful workflow
skill from a meeting summary. If that session is attached to a learning space,
Acontext's configured learning behavior applies to the imported context too.

## Setup

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Choose an existing Acontext session in your project and set `ACONTEXT_API_KEY` in
your environment before sending. Do not place the key in source files or chat.

## Export one selected meeting

Keep Screenpipe running locally. Review one completed meeting and obtain its ID.
Set `SCREENPIPE_LOCAL_API_KEY` to the recorder's local API key (available via
`screenpipe auth token` or the desktop app's configured connection). In a private
working directory, replace `42` with the selected ID:

```bash
umask 077
curl --fail --silent --show-error --max-time 10 --noproxy '*' \
  --header "Authorization: Bearer $SCREENPIPE_LOCAL_API_KEY" \
  http://127.0.0.1:3030/meetings/42 > meeting.json
```

This reads the authenticated local API, not Screenpipe's live SQLite database.
The script uses only `id`, `meeting_start`, `meeting_end` and `note`. Review and
edit `note` in the exported copy before sending; other fields are discarded.
An active meeting or missing note is rejected. Screenpipe access restrictions
still apply to the export request.

## Preview, then send

Replace the example session UUID with your own, and use a stable device label so
meeting IDs from different installations remain distinguishable:

```bash
uv run python main.py --meeting-json meeting.json --device work-laptop \
  --session-id 7c0896e0-2f5e-4f3c-8835-49123757ce7d
```

The preview makes no network requests. It prints the selected content to your
terminal, so do not save its output in shared logs. You can try the same command
with `meeting.example.json`, which contains synthetic data, without an API key.

After reviewing the preview, repeat with `--send`:

```bash
uv run python main.py --meeting-json meeting.json --device work-laptop \
  --session-id 7c0896e0-2f5e-4f3c-8835-49123757ce7d --send
```

Sending uploads the note to the SDK's configured endpoint (Acontext Cloud by
default; `ACONTEXT_BASE_URL` can select a self-hosted server). Check that variable
before sending. The SDK uses the project selected by your API key. The output contains the saved
message ID; inspect the session in Acontext before relying on the context in an
agent run. This example does not execute an agent or verify later recall quality.

Each send appends a message. There is no automatic deduplication, retry or deletion
sync. If the request fails without a confirmed result, inspect the target session
before retrying. Remove imported messages separately when removing their source
recordings. Never commit exports or real notes to this examples repository.

## Validation

```bash
uv run pytest -q
uv run ruff check main.py test_main.py
uv run ruff format --check main.py test_main.py
```

Tests use synthetic data, a stubbed SDK boundary and the real SDK with a mock HTTP
transport. They cover preview-only behavior,
selected-field projection, provenance, invalid or unfinished meetings, explicit
sending, missing credentials and errors that do not print note content or keys.
