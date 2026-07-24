# Teler 

This library offers a lightweight and developer-friendly abstraction over the FreJun Teler API.

## What is Teler?

Teler is a programmable voice API by FreJun. It handles carriers, phone numbers, and real-time audio streaming so you can connect AI models directly to phone calls. → [frejun.ai](https://frejun.ai)

## Basic Usage

The built-in client interfaces provide methods for creating and managing Teler's REST resources.

### Client (Synchronous)

```python
from teler import Client

TELER_API_KEY = 'API_KEY'
client = Client(TELER_API_KEY)

call = client.calls.create(
    from_number="+123*******",
    to_number="+456*******",
    flow_url="https://example.com/flow",
    status_callback_url="https://example.com/status",
    record=True,
)
```

### AsyncClient (Asynchronous)

```python
from teler import AsyncClient

TELER_API_KEY = 'API_KEY'
client = AsyncClient(TELER_API_KEY)

async def initiate_call()
    call = await client.calls.create(
        from_number="+123*******",
        to_number="+456*******",
        flow_url="https://example.com/flow",
        status_callback_url="https://example.com/status",
        record=True,
    )

asyncio.run(initiate_call())
```

## Media Streaming

The library provides a simple interface for integrating real-time call audio streams from Teler into your application, unlocking advanced capabilities such as Conversational AI, Real-time transcription, and Actionable insights.

### `StreamConnector`

This class lets you bridge the call audio stream to your desired websocket endpoint. It handles message relaying between the two streams via pluggable handlers, making it highly customizable.
It also handles graceful shutdown of the media streams in case of any unexpected errors.

It takes the following 4 parameters:

1. **stream_type** - Only `StreamType.BIDIRECTIONAL` is supported for now.
2. **remote_url** - The remote websocket URL where the call audio stream needs to be bridged.
3. **call_stream_handler** - A `StreamHandler` coroutine that handles the call audio stream.
4. **remote_stream_handler** - A `StreamHandler` coroutine that handles the remote audio stream.

### `StreamHandler`

A `StreamHandler` coroutine receives the incoming messages on the websocket, processes them and returns a tuple of `(str, StreamOp)` where `StreamOp` is an operation flag that decides the subsequent action the `StreamConnector` will take.

`StreamOp` can be one of:

1. **StreamOp.RELAY** - Relays the message to the other stream. The message needs to be supplied as a string as the first item in the returned tuple.
2. **StreamOp.PASS** - Does not relay any message to the other stream. Any message in the returned tuple will be ignored.
3. **StreamOp.STOP** - Stops both streams, ends the call and exits gracefully. Any message in the returned tuple will be ignored.   

## Sample Application - Implementing AI-driven outbound calling using Teler and Elevenlabs

The following application utilizes the Teler SDK to start a call and bridge its audio stream to an ElevenLabs AI agent that responds in real time. The response is then streamed back to Teler and played over the call.


```python
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Body, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Annotated

from teler.streams import StreamConnector, StreamOp, StreamType
from teler import AsyncClient, CallFlow

router = APIRouter()
logger = logging.getLogger(__name__)

# Global variables
ELEVENLABS_AGENT_ID = "agent_*****"
ELEVENLABS_WEBSOCKET_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={ELEVENLABS_AGENT_ID}"

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
    return ({}, StreamOp.PASS)

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
        return ({}, StreamOp.PASS)

    return handler

connector = StreamConnector(
    stream_type=StreamType.BIDIRECTIONAL,
    remote_url=ELEVENLABS_WEBSOCKET_URL,
    call_stream_handler=call_stream_handler,
    remote_stream_handler=remote_stream_handler(),
)

@router.post("/flow", status_code=status.HTTP_200_OK, include_in_schema=False)
async def stream_flow(payload: CallFlowRequest):
    """
    Build and return Stream flow.
    """
    stream_flow = CallFlow.stream(
        ws_url=f"wss://{BACKEND_DOMAIN}/media-stream",
        chunk_size=500,
        record=True
    )
    return JSONResponse(stream_flow)

@router.post("/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def webhook_receiver(data: Annotated[dict, Body()]):
    logger.info(f"--------Webhook Payload-------- {data}")
    return JSONResponse(content="Webhook received.")

@router.post("/initiate-call", status_code=status.HTTP_200_OK)
async def initiate_call():
    """
    Initiate a call using Teler SDK.
    """
    try:
        async with AsyncClient(api_key=TELER_API_KEY, timeout=10) as client:
            call = await client.calls.create(
                from_number=f"{FROM_NUMBER}",
                to_number=f"{TO_NUMBER}",
                flow_url=f"https://{BACKEND_DOMAIN}/flow",
                status_callback_url=f"https://{BACKEND_DOMAIN}/webhook",
                record=True,
            )
            logger.info(f"Call created: {call}")
        return JSONResponse(content={"success": True})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create call.")

@router.websocket("/media-stream")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected.")
    await connector.bridge_stream(websocket)
```
