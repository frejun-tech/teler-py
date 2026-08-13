import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.voice.types import TransferResource

BASE = "https://api.frejun.ai/api/v1"

TRANSFER_JSON = {
    "id": "op_1",
    "call_id": "cs_1",
    "status": "accepted",
    "target_leg_id": "cl_2",
    "mode": "cold",
    "request_id": "req_1",
}

TARGET = {"kind": "pstn", "number": "+15550001111"}
ACTION = {"action": "play", "media_url": "https://example.com/hold.mp3"}


def test_transfer_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_1/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        op = client.voice.operations.transfer(
            "cs_1", target=TARGET, mode="cold", dial_music=ACTION
        )

        assert route.called
        request = route.calls.last.request
        body = json.loads(request.content)
        assert body["target"] == TARGET
        assert body["mode"] == "cold"
        assert body["dial_music"] == ACTION
        assert request.headers["Idempotency-Key"]
        assert isinstance(op, TransferResource)
        assert op.id == "op_1"


def test_transfer_forwards_explicit_idempotency_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_1/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = Client(api_key="test_api_key")

        client.voice.operations.transfer(
            "cs_1", target=TARGET, mode="cold", idempotency_key="key-123"
        )

        assert route.calls.last.request.headers["Idempotency-Key"] == "key-123"


def test_transfer_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/cs_1/transfer").mock(
            return_value=httpx.Response(202, json={"data": TRANSFER_JSON})
        )
        client = Client(api_key="test_api_key")

        op = client.voice.operations.transfer("cs_1", target=TARGET, mode="cold")

        assert isinstance(op, TransferResource)
        assert op.id == "op_1"


@pytest.mark.asyncio
async def test_async_transfer_accepts_dict_actions():
    """The async signature must take plain dicts; a dataclass is not JSON
    serializable and would raise inside httpx."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/cs_1/transfer").mock(
            return_value=httpx.Response(202, json=TRANSFER_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        op = await client.voice.operations.transfer(
            "cs_1",
            target=TARGET,
            mode="cold",
            dial_music=ACTION,
            confirm_sound=ACTION,
            on_failure=ACTION,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["dial_music"] == ACTION
        assert body["confirm_sound"] == ACTION
        assert body["on_failure"] == ACTION
        assert isinstance(op, TransferResource)


def test_transfer_signatures_match_between_sync_and_async():
    import inspect

    from teler.resources.voice.operations import (
        AsyncOperationResourceManager, OperationResourceManager)

    sync_params = inspect.signature(OperationResourceManager.transfer).parameters
    async_params = inspect.signature(AsyncOperationResourceManager.transfer).parameters

    assert list(sync_params) == list(async_params)
    for name in sync_params:
        assert sync_params[name].annotation == async_params[name].annotation, name
