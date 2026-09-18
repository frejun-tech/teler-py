import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.voice.types import TransferResource

BASE = "https://api.frejun.ai/api/v1"

TRANSFER_JSON = {
    "id": "op_123",
    "call_id": "cs_123",
    "status": "initiated",
    "target_leg_id": None,
    "mode": "cold",
    "request_id": "req_123",
}

TRANSFER_WARM_JSON = {
    "id": "op_456",
    "call_id": "cs_456",
    "status": "initiated",
    "target_leg_id": "cl_789",
    "mode": "warm",
    "request_id": "req_456",
}


# --- transfer ---
def test_voice_operations_transfer_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "pstn"
        assert body["target"]["number"] == "+15550003333"
        assert body["mode"] == "cold"
        assert isinstance(result, TransferResource)
        assert result.id == "op_123"
        assert result.mode == "cold"


def test_voice_operations_transfer_cold_mode():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550004444"},
            mode="cold",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["mode"] == "cold"
        assert isinstance(result, TransferResource)
        assert result.mode == "cold"


def test_voice_operations_transfer_warm_mode():
    # The API rejects every mode other than "cold" with a 400.
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/cs_456/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_WARM_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_456",
            target={"kind": "pstn", "number": "+15550005555"},
            mode="warm",
        )

        assert isinstance(result, TransferResource)
        assert result.mode == "warm"
        assert result.status == "initiated"


def test_voice_operations_transfer_to_sip_target():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={
                "kind": "sip",
                "uri": "sip:user@example.com:5060",
            },
            mode="cold",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "sip"
        assert body["target"]["uri"] == "sip:user@example.com:5060"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_to_leg():
    # The API does not support leg targets yet and 400s on them.
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={
                "kind": "leg",
                "leg_id": "cl_999",
            },
            mode="cold",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "leg"
        assert body["target"]["leg_id"] == "cl_999"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_ringback():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            ringback="passthrough",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["ringback"] == "passthrough"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_dial_music():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            dial_music={
                "action": "play",
                "media_url": "https://example.com/music.mp3",
            },
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["dial_music"]["action"] == "play"
        assert body["dial_music"]["media_url"] == "https://example.com/music.mp3"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_timeout():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            timeout=30,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["timeout"] == 30
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_record():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            record=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["record"] is True
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_confirm_sound():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            confirm_sound={
                "action": "say",
                "text": "Call transferred",
                "voice": "male",
                "language": "en-US",
            },
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["confirm_sound"]["action"] == "say"
        assert body["confirm_sound"]["text"] == "Call transferred"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_on_failure():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
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
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            idempotency_key="idem_xfer_123",
        )

        assert route.called
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_xfer_123"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_custom_headers():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={
                "kind": "sip",
                "uri": "sip:user@example.com",
                "custom_headers": {
                    "X-Custom-Header": "value",
                    "X-Another-Header": "another",
                },
            },
            mode="cold",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["custom_headers"]["X-Custom-Header"] == "value"
        assert isinstance(result, TransferResource)


def test_voice_operations_transfer_with_all_options():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
            timeout=30,
            record=True,
            ringback="passthrough",
            dial_music={"action": "play", "media_url": "https://example.com/music.mp3"},
            confirm_sound={"action": "say", "text": "Transferred"},
            on_failure={"action": "hangup"},
            idempotency_key="idem_full",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["target"]["kind"] == "pstn"
        assert body["mode"] == "cold"
        assert body["timeout"] == 30
        assert body["record"] is True
        assert body["ringback"] == "passthrough"
        assert isinstance(result, TransferResource)


@pytest.mark.asyncio
async def test_async_voice_operations_transfer_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
        )

        assert route.called
        assert isinstance(result, TransferResource)
        assert result.id == "op_123"


# --- data envelope unwrapping ---
def test_voice_operations_transfer_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json={"data": TRANSFER_JSON})
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
        )

        assert isinstance(result, TransferResource)
        assert result.id == "op_123"
        assert result.mode == "cold"


# --- edge cases ---
def test_voice_operations_transfer_returns_status():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/cs_123/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_WARM_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.operations.transfer(
            "cs_123",
            target={"kind": "pstn", "number": "+15550003333"},
            mode="cold",
        )

        assert isinstance(result, TransferResource)
        assert result.status == "initiated"
        assert result.target_leg_id == "cl_789"
