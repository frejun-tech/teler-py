import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.voice.types import TransferResource

BASE = "https://api.frejun.ai/api/v1"

TRANSFER_JSON = {
    "id": "xfer_123",
    "call_id": "vc_123",
    "status": "initiated",
    "target_leg_id": None,
    "mode": "bridge",
    "request_id": "req_123",
}

TRANSFER_COMPLETED_JSON = {
    "id": "xfer_456",
    "call_id": "vc_456",
    "status": "completed",
    "target_leg_id": "leg_789",
    "mode": "supervised",
    "request_id": "req_456",
}


# --- transfer ---
def test_voice_operations_transfer_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "number"
        assert body["target"]["number"] == "+15550003333"
        assert body["mode"] == "bridge"
        assert isinstance(result, TransferResource)
        assert result.id == "xfer_123"
        assert result.mode == "bridge"


def test_voice_operations_transfer_bridge_mode():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550004444"},
            mode="bridge",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["mode"] == "bridge"
        assert isinstance(result, TransferResource)
        assert result.mode == "bridge"


def test_voice_operations_transfer_supervised_mode():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/vc_456/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_COMPLETED_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_456",
            target={"kind": "number", "number": "+15550005555"},
            mode="supervised",
        )

        assert isinstance(result, TransferResource)
        assert result.mode == "supervised"
        assert result.status == "completed"


def test_voice_operations_transfer_to_sip_uri():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={
                "kind": "sip_uri",
                "uri": "sip:user@example.com:5060",
            },
            mode="bridge",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "sip_uri"
        assert body["target"]["uri"] == "sip:user@example.com:5060"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_to_leg():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={
                "kind": "leg",
                "leg_id": "leg_999",
            },
            mode="bridge",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "leg"
        assert body["target"]["leg_id"] == "leg_999"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_ringback():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            ringback="https://example.com/ringback.mp3",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["ringback"] == "https://example.com/ringback.mp3"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_dial_music():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            dial_music={
                "kind": "file",
                "url": "https://example.com/music.mp3",
            },
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["dial_music"]["kind"] == "file"
        assert body["dial_music"]["url"] == "https://example.com/music.mp3"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_timeout():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            timeout=30,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["timeout"] == 30
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_record():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            record=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["record"] is True
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_confirm_sound():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="supervised",
            confirm_sound={
                "kind": "text",
                "text": "Call transferred",
                "voice": "male",
                "language": "en-US",
            },
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["confirm_sound"]["kind"] == "text"
        assert body["confirm_sound"]["text"] == "Call transferred"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_on_failure():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            on_failure={
                "action": "hangup",
                "reason": "transfer_failed",
            },
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["on_failure"]["action"] == "hangup"
        assert body["on_failure"]["reason"] == "transfer_failed"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_idempotency_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            idempotency_key="idem_xfer_123",
        )

        assert route.called
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_xfer_123"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_custom_headers():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={
                "kind": "sip_uri",
                "uri": "sip:user@example.com",
                "custom_headers": {
                    "X-Custom-Header": "value",
                    "X-Another-Header": "another",
                },
            },
            mode="bridge",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["custom_headers"]["X-Custom-Header"] == "value"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_all_options():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
            timeout=30,
            record=True,
            ringback="https://example.com/ringback.mp3",
            dial_music={"kind": "silence"},
            confirm_sound={"kind": "text", "text": "Transferred"},
            on_failure={"action": "hangup"},
            idempotency_key="idem_full",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "number"
        assert body["mode"] == "bridge"
        assert body["timeout"] == 30
        assert body["record"] is True
        assert body["ringback"] == "https://example.com/ringback.mp3"
        assert isinstance(result, TransferResource)


@pytest.mark.asyncio
async def test_async_voice_operations_transfer_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
        )

        assert route.called
        assert isinstance(result, TransferResource)
        assert result.id == "xfer_123"


# --- data envelope unwrapping ---
def test_voice_operations_transfer_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json={"data": TRANSFER_JSON})
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
        )

        assert isinstance(result, TransferResource)
        assert result.id == "xfer_123"
        assert result.mode == "bridge"


# --- edge cases ---
def test_voice_operations_transfer_returns_status():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/vc_123/transfer").mock(
            return_value=httpx.Response(200, json=TRANSFER_COMPLETED_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "vc_123",
            target={"kind": "number", "number": "+15550003333"},
            mode="bridge",
        )

        assert isinstance(result, TransferResource)
        assert result.status == "completed"
        assert result.target_leg_id == "leg_789"
