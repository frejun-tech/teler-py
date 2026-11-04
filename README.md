# Teler Python SDK

This Python library offers a lightweight and developer-friendly abstraction over the FreJun Teler API.

## What is Teler?

Teler is a programmable voice API by FreJun. It handles carriers, phone numbers, and real-time audio streaming so you can connect AI models directly to phone calls. → [frejun.ai](https://frejun.ai)

## Requirements

- Python 3.9 or later
- pip

## Features

- **Initiate Calls** — Start outbound calls using the Teler REST API.
- **Call Flows** — Control call behavior with `CallFlow` helpers (`stream`, `play`, `hangup`, `dial`).
- **Call Controls & Mutations** — Manage live calls in real time with `mute`, `DTMF`, `playback`, and `transfer`.
- **Real-time Media Streaming** — Bridge call audio via WebSockets using `StreamConnector` for Conversational AI, transcription, and insights.
- **Voice Apps & Virtual Numbers** — Configure call routing and manage virtual numbers.
- **SIP Trunking & IP ACLs** — Connect your own carrier/PBX and manage IP access control lists.
- **Secrets & Webhooks** — Create and rotate secrets to authenticate incoming webhooks from Teler.
- **Sync and Async Clients** — The same API surface for both.
- **Typed Errors** — Catch specific exceptions instead of parsing HTTP responses.

## Installation

```bash
pip install teler
```

For a local checkout:

```bash
pip install -e ".[test]"
```

## Basic Usage

The built-in client interfaces provide methods for creating and managing Teler's REST resources.

### Client (Synchronous)

```python
from teler import Client

TELER_API_KEY = "API_KEY"
client = Client(TELER_API_KEY)

call = client.voice.calls.create(
    from_number="+123*******",
    to_number="+456*******",
    flow_url="https://example.com/flow",
    status_callback_url="https://example.com/status",
    record=True,
)
```

### AsyncClient (Asynchronous)

```python
import asyncio

from teler import AsyncClient

TELER_API_KEY = "API_KEY"


async def initiate_call():
    async with AsyncClient(api_key=TELER_API_KEY) as client:
        return await client.voice.calls.create(
            from_number="+123*******",
            to_number="+456*******",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/status",
            record=True,
        )


call = asyncio.run(initiate_call())
```

Both clients are context managers, so the underlying HTTP connection pool is closed
when the block exits. `Client.close()` and `AsyncClient.aclose()` do the same thing
explicitly.

### Client Configuration

```python
client = Client(
    api_key="YOUR_API_KEY",
    headers={"X-Trace-Id": "trace-123"},   # override SDK defaults
    base_url="https://api.frejun.ai/api/v1",
    timeout=10,                             # seconds
)
```

Headers passed to the constructor override the SDK defaults (`Content-Type`,
`Accept`, `User-Agent`), matched case-insensitively. `x-api-key` is always taken
from `api_key` and cannot be displaced by a header.

`timeout` is passed through to `httpx`. Values greater than `1000` are treated as
milliseconds, so `timeout=10` and `timeout=10000` both mean ten seconds. Any other
keyword argument is forwarded to `httpx.Client` / `httpx.AsyncClient`.

The client defaults to the production API. Set `TELER_BACKEND_DOMAIN` to point a
whole process at another deployment:

```bash
export TELER_BACKEND_DOMAIN="https://staging.frejun.ai"
```

The value is the scheme and host only — the SDK appends `/api/v1`. It is read
when `teler` is imported, so it must be set before the import. A `base_url`
argument to `Client` or `AsyncClient` wins over the environment variable, and
the environment variable wins over the production default.

## Resources

Both `Client` and `AsyncClient` expose the same namespaces, with identical method
names — the async versions are awaitable.

| Namespace | Methods |
|---|---|
| `client.voice.calls` | `create`, `list`, `retrieve`, `list_legs` |
| `client.voice.apps` | `create`, `list`, `retrieve`, `update`, `delete`, `list_virtual_numbers` |
| `client.voice.mutations` | `play`, `dtmf`, `mute`, `hangup` |
| `client.voice.operations` | `transfer` |
| `client.virtual_numbers` | `list`, `assign`, `unassign`, `update` |
| `client.sip.trunks` | `create`, `list`, `retrieve`, `update`, `delete`, `list_virtual_numbers` |
| `client.sip.calls` | `list`, `retrieve` |
| `client.sip.ip_acls` | `create`, `list`, `retrieve`, `update`, `delete` |
| `client.secrets` | `create`, `list`, `retrieve`, `update`, `delete` |
| `client.events` | `list`, `retrieve`, `redeliver` |
| `client.recordings` | `retrieve` |

Every resource keeps the full response body on `.raw`. Fields the SDK does not
declare are ignored rather than raising, so a field added by the API does not break
an existing call.

## Webhook API Version

Voice apps and SIP trunks pin the version of the webhook payloads Teler sends them.
Only `2026-06-01` is supported. New resources default to it; passing any other
value, including the retired `2025-08-01`, raises `BadParametersException` before
the request is sent.

Existing resources created against the retired version must be migrated:

```python
client.voice.apps.update(app_id, webhook_api_version="2026-06-01")
client.sip.trunks.update(trunk_id, webhook_api_version="2026-06-01")
```

Version `2026-06-01` also changes the call ID returned by call initiation from the
raw upstream UUID to a `cs_...` session ID, and call controls require it.

## Field Naming

The SDK uses `snake_case` for everything — request arguments, request bodies,
response fields, and resource attributes. This matches the API's wire format, so no
key conversion is performed.

```python
call = client.voice.calls.create(
    from_number="+918065xxxx",
    to_number="+919967xxxx",
    flow_url="https://your-domain.com/flow",
    status_callback_url="https://your-domain.com/receiver",
    record=True,
)
```

User- or server-defined key/value bags such as `custom_headers`, `properties`, and
`payload` are passed through untouched.

## Pagination

List endpoints return a single `CursorPage`:

```python
page = client.voice.calls.list(limit=50)

page.data              # list of CallResource
page.next_cursor       # cursor for the next page, or None
page.previous_cursor   # cursor for the previous page, or None
page.has_more          # whether more pages are available
```

To iterate over everything, follow `next_cursor`:

```python
page = client.voice.calls.list(limit=50)

while True:
    for call in page.data:
        print(call.id, call.state)

    if not page.has_more or not page.next_cursor:
        break

    page = client.voice.calls.list(limit=50, cursor_after=page.next_cursor)
```

The async version is identical apart from the `await`:

```python
async def list_all_calls():
    page = await client.voice.calls.list(limit=50)

    while True:
        for call in page.data:
            print(call.id, call.state)

        if not page.has_more or not page.next_cursor:
            return

        page = await client.voice.calls.list(
            limit=50, cursor_after=page.next_cursor
        )
```

`cursor_after` and `cursor_before` are mutually exclusive. Limits are validated
client-side: 1–100 for most endpoints and 1–50 for the voice-app and SIP-trunk
virtual-number listings. Most list methods default to 50 results; virtual-number
listings and secrets default to 10.

There is no auto-pagination helper today — follow `next_cursor` as above.

## Call Initiation with Idempotency

`create()` accepts optional keyword arguments for idempotency, retries, and retry
timing:

```python
call = client.voice.calls.create(
    from_number="+918065xxxx",
    to_number="+919967xxxx",
    flow_url="https://your-domain.com/flow",
    status_callback_url="https://your-domain.com/receiver",
    record=True,
    idempotency_key="my-unique-idempotency-key",  # optional, <= 255 chars
    retry=True,                                    # optional, default: False
    base_retry_delay_ms=300,                       # optional, default: 300
)
```

**Parameters:**

- `idempotency_key` — (Optional, <= 255 chars) Unique key for this operation. If
  omitted, the SDK generates a random UUID v4. Use the same key when retrying the
  same logical operation. An empty or over-long key raises
  `BadParametersException` before the request is sent.
- `retry` — (Optional, default `False`) Retry on network errors and 429/503
  responses.
- `base_retry_delay_ms` — (Optional, default `300`) Base delay for exponential
  backoff with jitter, capped at 2000 ms.

Call initiation requests use a 5-second timeout.

If you omit `idempotency_key`, the SDK auto-generates a UUID, making SDK-internal
retries safe. For application-level retries (after a timeout or crash), generate
and reuse your own key:

```python
import uuid

idempotency_key = str(uuid.uuid4())  # generate once

call = client.voice.calls.create(
    from_number="+918065xxxx",
    to_number="+919967xxxx",
    flow_url="https://your-domain.com/flow",
    status_callback_url="https://your-domain.com/receiver",
    idempotency_key=idempotency_key,
    retry=True,
)

# If this call needs to be retried, use the same idempotency_key.
```

Requests other than call initiation and call control retry as follows: `GET` and
`DELETE` retry by default (three retries, 100 ms base delay); `POST` and `PATCH`
are opt-in. When the API sends a `Retry-After` header on a 429 or 503, the SDK
waits for that duration instead of the computed backoff.

## Call Flows

When a call connects, Teler fetches instructions from your `flow_url`. Build the
response with `CallFlow` or return the equivalent JSON yourself.

### Stream

```python
from teler import CallFlow

flow = CallFlow.stream(
    "wss://your-domain.com/stream",
    sample_rate="8k",
    chunk_size=400,
    record=True,
)
```

Equivalent JSON:

```json
{
  "action": "stream",
  "ws_url": "wss://your-domain.com/stream",
  "sample_rate": "8k",
  "chunk_size": 400,
  "record": true
}
```

### Play

```python
flow = CallFlow.play(
    "https://example.com/audio.mp3",
    "https://example.com/next-flow",
)
```

Equivalent JSON:

```json
{
  "action": "play",
  "media_url": "https://example.com/audio.mp3",
  "flow_url": "https://example.com/next-flow"
}
```

`flow_url` is optional. When supplied, Teler requests the next flow from it once
playback finishes (beta).

### Dial

```python
flow = CallFlow.dial(
    "+919967xxxx",
    timeout=30,
    record=True,
    status_callback_url="https://example.com/status",
    custom_headers={"X-Customer-Id": "cust_123"},
)
```

Equivalent JSON:

```json
{
  "action": "dial",
  "to": "+919967xxxx",
  "timeout": 30,
  "record": true,
  "status_callback_url": "https://example.com/status",
  "custom_headers": { "X-Customer-Id": "cust_123" }
}
```

`to` is one E.164 number or SIP URI. `record` accepts `False`, `True`, `"stereo"`,
`"mono"` or `"per_leg"`. `custom_headers` keys must start with `X-`; at most 16
headers with values up to 256 bytes. `dial` also accepts `ringback`
(`"passthrough"` / `"suppress"`), `dial_music`, `confirm_sound`, `on_no_answer`,
`on_busy` and `on_failure`, each a nested `play` or `hangup` action.

This action requires the owning voice app to be pinned to webhook version
`2026-06-01`.

### Hangup

```python
flow = CallFlow.hangup()
```

Equivalent JSON:

```json
{ "action": "hangup" }
```

## Call Controls & Mutations

```python
# Mute or unmute a specific leg
client.voice.mutations.mute(
    call_id,
    leg_id="leg_123",
    on=True,
)

# Send DTMF tones
client.voice.mutations.dtmf(
    call_id,
    digits="123#",
    leg_id="leg_123",
)

# Play audio into the call
client.voice.mutations.play(
    call_id,
    media_url="https://example.com/audio.mp3",
    leg_id="leg_123",
)

# End the call, or a single leg
client.voice.mutations.hangup(
    call_id,
    leg_id="leg_123",
)

# Transfer the call
client.voice.operations.transfer(
    call_id,
    target={"kind": "pstn", "number": "+919967xxxx"},
    mode="cold",
)
```

`AsyncClient` exposes the same methods as coroutines:

```python
async def mute_leg():
    await client.voice.mutations.mute(call_id, leg_id="leg_123", on=True)
```

Call-control requests use a 5-second timeout and a 300 ms base retry delay.

### Idempotency Keys

Every mutation and `transfer` accepts three optional trailing arguments:

```python
client.voice.mutations.hangup(
    call_id,
    leg_id="leg_123",
    idempotency_key="my-own-key",
    retry=True,
    base_retry_delay_ms=300,
)
```

`idempotency_key` is auto-generated as a UUID v4 when omitted. That makes the
SDK's own retries safe, but not retries performed by your application. For those,
generate and reuse your own key:

```python
import uuid

idempotency_key = str(uuid.uuid4())

client.voice.mutations.hangup(
    call_id,
    leg_id="leg_123",
    idempotency_key=idempotency_key,
)
```

## Media Streaming

The library provides a simple interface for integrating real-time call audio
streams from Teler into your application, unlocking advanced capabilities such as
Conversational AI, real-time transcription, and actionable insights.

### StreamConnector

`StreamConnector` bridges the Teler call WebSocket to a remote WebSocket, such as
an AI agent or transcription service.

```python
from teler import StreamConnector, StreamOp
from teler.streams import StreamType

connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url="wss://your-ai-agent.example.com/stream",
    call_stream_handler=on_call_message,
    remote_stream_handler=on_remote_message,
)
```

It takes five parameters:

1. **`stream_type`** — Only `StreamType.BIDIRECTIONAL` is supported today.
   `StreamType.UNIDIRECTIONAL` raises `NotImplementedException`.
2. **`remote_url`** — The remote WebSocket URL where the call audio stream is
   bridged.
3. **`call_stream_handler`** — An async handler for messages from the Teler call
   stream.
4. **`remote_stream_handler`** — An async handler for messages from the remote
   stream.
5. **`remote_headers`** — A dict of extra HTTP headers sent in the WebSocket
   handshake to `remote_url`. Use it for bearer tokens or API keys. Defaults to
   no extra headers.

Both handlers default to relaying every message unchanged. `remote_headers` is
sent only while opening the connection to `remote_url`; it is not forwarded to
the Teler call stream.

Bridge the call WebSocket:

```python
async def handle_call(call_ws):
    await connector.bridge_stream(call_ws)
```

`call_ws` must expose `iter_text()`, `send()`, `send_text()` and `close()` — a
FastAPI/Starlette `WebSocket` works as-is. When either side stops, the other task
is cancelled and the remote socket is closed.

Authenticated remote endpoints pass their credentials through `remote_headers`:

```python
connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url="wss://api.elevenlabs.io/v1/convai/conversation",
    remote_headers={"xi-api-key": ELEVENLABS_API_KEY},
)
```

### Stream Handlers

A `StreamHandler` is an async callable:

```python
async def handler(message: str) -> tuple[str, StreamOp]:
    ...
```

It receives the raw message as a `str` and returns `(data, stream_op)`. `data` must
be a `str` when the operation is `StreamOp.RELAY`; it is ignored otherwise.

### StreamOp

`StreamOp` decides what the connector does with the handler's result:

- **`StreamOp.RELAY`** — Relay `data` to the other stream.
- **`StreamOp.PASS`** — Do not relay anything. Return `("", StreamOp.PASS)`.
- **`StreamOp.STOP`** — Stop both streams, end the call, and exit gracefully.

### Example

```python
import logging

from teler import StreamConnector, StreamOp
from teler.streams import StreamType

logging.basicConfig(level=logging.INFO)


async def on_call_message(message: str):
    print("From Teler:", message)
    return (message, StreamOp.RELAY)


async def on_remote_message(message: str):
    print("From agent:", message)
    return (message, StreamOp.RELAY)


connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url="wss://your-ai-agent.example.com/stream",
    call_stream_handler=on_call_message,
    remote_stream_handler=on_remote_message,
)


async def bridge(call_ws):
    await connector.bridge_stream(call_ws)
```

## Sample Application - Implementing AI-driven outbound calling using Teler and ElevenLabs

The following application uses the Teler SDK to start a call and bridge its audio
stream to an ElevenLabs AI agent that responds in real time. The response is then
streamed back to Teler and played over the call.

```python
import json
import logging

from fastapi import APIRouter, WebSocket, Body, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Annotated

from teler.streams import StreamConnector, StreamOp, StreamType
from teler import AsyncClient, CallFlow

router = APIRouter()
logger = logging.getLogger(__name__)

# Global variables
ELEVENLABS_AGENT_ID = "agent_*****"
ELEVENLABS_API_KEY = "ELEVENLABS_API_KEY"
ELEVENLABS_WEBSOCKET_URL = (
    "wss://api.elevenlabs.io/v1/convai/conversation"
    f"?agent_id={ELEVENLABS_AGENT_ID}"
)

TELER_API_KEY = "TELER_API_KEY"
BACKEND_DOMAIN = "example.com"
FROM_NUMBER = "+91123*******"
TO_NUMBER = "+91456*******"


class CallFlowRequest(BaseModel):
    call_id: str
    account_id: str
    from_number: str
    to_number: str


async def call_stream_handler(message: str):
    msg = json.loads(message)
    if msg["type"] == "audio":
        payload = json.dumps({"user_audio_chunk": msg["data"]["audio_b64"]})
        return (payload, StreamOp.RELAY)
    return ("", StreamOp.PASS)


def remote_stream_handler():
    chunk_id = 1

    async def handler(message: str):
        nonlocal chunk_id
        msg = json.loads(message)
        if msg["type"] == "audio":
            payload = json.dumps(
                {
                    "type": "audio",
                    "audio_b64": msg["audio_event"]["audio_base_64"],
                    "chunk_id": chunk_id,
                }
            )
            chunk_id += 1
            return (payload, StreamOp.RELAY)
        elif msg["type"] == "interruption":
            payload = json.dumps({"type": "clear"})
            return (payload, StreamOp.RELAY)
        return ("", StreamOp.PASS)

    return handler


connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url=ELEVENLABS_WEBSOCKET_URL,
    remote_headers={"xi-api-key": ELEVENLABS_API_KEY},
    call_stream_handler=call_stream_handler,
    remote_stream_handler=remote_stream_handler(),
)


@router.post("/flow", status_code=status.HTTP_200_OK, include_in_schema=False)
async def stream_flow(payload: CallFlowRequest):
    """Build and return the stream flow."""
    flow = CallFlow.stream(
        ws_url=f"wss://{BACKEND_DOMAIN}/media-stream",
        chunk_size=500,
        record=True,
    )
    return JSONResponse(flow)


@router.post("/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def webhook_receiver(data: Annotated[dict, Body()]):
    logger.info("--------Webhook Payload-------- %s", data)
    return JSONResponse(content="Webhook received.")


@router.post("/initiate-call", status_code=status.HTTP_200_OK)
async def initiate_call():
    """Initiate a call using the Teler SDK."""
    try:
        async with AsyncClient(api_key=TELER_API_KEY, timeout=10) as client:
            call = await client.voice.calls.create(
                from_number=FROM_NUMBER,
                to_number=TO_NUMBER,
                flow_url=f"https://{BACKEND_DOMAIN}/flow",
                status_callback_url=f"https://{BACKEND_DOMAIN}/webhook",
                record=True,
            )
            logger.info("Call created: %s", call.id)
        return JSONResponse(content={"success": True})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create call.",
        )


@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected.")
    await connector.bridge_stream(websocket)
```

## Logging

The SDK uses Python's standard `logging` module and is silent by default.

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("teler").setLevel(logging.DEBUG)
```

`StreamConnector` logs connection lifecycle events at `INFO` and individual stream
messages at `DEBUG`. There is no logger object to pass to the client.

## Error Handling

The SDK raises typed exceptions that extend `TelerException`.

### Exception Hierarchy

```text
TelerException (base)
├── BadParametersException (400)
├── UnauthorizedException (401)
├── ForbiddenException (403)
├── NotFoundException (404)
├── ConflictException (409)
├── GoneException (410)
├── UnprocessableRequestException (422)
├── RateLimitException (429)
├── InternalServerErrorException (500)
└── NotImplementedException (501)
```

Any unmapped 4xx/5xx status raises the base `TelerException`.

### Exception Reference

| Exception | Status | Description |
|---|---|---|
| `TelerException` | — | Base exception; also raised for unmapped statuses |
| `BadParametersException` | `400` | Invalid request parameters, or client-side validation failure |
| `UnauthorizedException` | `401` | Invalid or missing API key |
| `ForbiddenException` | `403` | Authenticated but not allowed |
| `NotFoundException` | `404` | Resource does not exist |
| `ConflictException` | `409` | Resource conflicts with current state |
| `GoneException` | `410` | Resource is no longer available |
| `UnprocessableRequestException` | `422` | Request body failed validation |
| `RateLimitException` | `429` | Rate limit exceeded |
| `InternalServerErrorException` | `500` | Internal server error |
| `NotImplementedException` | `501` | Feature is not implemented |

### Properties

All exceptions expose:

- `message` — human-readable error description.
- `code` — HTTP status code, or the default for the exception class.
- `details` — the API's `errors` array when the response body has one, otherwise
  `None`.
- `param` — the invalid parameter name. Populated for client-side validation
  errors raised as `BadParametersException`; it is not parsed from API error
  responses.

API error fields are returned as received; they are not renamed or converted.

### Validation Error Details

```python
from teler import exceptions

try:
    client.voice.calls.create(
        from_number="+918065xxxx",
        to_number="+919967xxxx",
        flow_url="https://your-domain.com/flow",
        status_callback_url="https://your-domain.com/receiver",
    )
except exceptions.UnprocessableRequestException as exc:
    print(exc.message)
    print(exc.code)       # 422
    print(exc.details)    # the API "errors" array, if present
```

Example `details` payload:

```json
[
  {
    "type": "string_too_short",
    "loc": ["body", "auth_credential", "username"],
    "msg": "String should have at least 5 characters",
    "input": "usr",
    "ctx": { "min_length": 5 }
  }
]
```

Network failures are not wrapped by the SDK. Catch the underlying `httpx`
exception:

```python
import httpx

try:
    client.voice.calls.create(...)
except httpx.RequestError as exc:
    print("Network failure:", exc)
```
