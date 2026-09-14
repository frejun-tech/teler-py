import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.voice.types import MutationResource

BASE = "https://api.frejun.ai/api/v1"

MUTATION_JSON = {
    "request_id": "req_123",
    "playback_id": None,
}

PLAYBACK_JSON = {
    "request_id": "req_456",
    "playback_id": "playback_123",
}

PLAYBACK_WITH_MEDIA_URL = {
    "request_id": "req_789",
    "playback_id": "playback_456",
}


# --- hangup ---
def test_voice_mutations_hangup_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.hangup(
            "vc_123",
            reason="normal_clearing",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["reason"] == "normal_clearing"
        assert "leg_id" not in body
        assert isinstance(result, MutationResource)
        assert result.request_id == "req_123"


def test_voice_mutations_hangup_with_leg_id():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.hangup(
            "vc_123",
            leg_id="leg_456",
            reason="call_rejected",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["leg_id"] == "leg_456"
        assert body["reason"] == "call_rejected"
        assert isinstance(result, MutationResource)


def test_voice_mutations_hangup_without_optional_fields():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.hangup("vc_123")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {}
        assert isinstance(result, MutationResource)


def test_voice_mutations_hangup_with_idempotency_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.hangup(
            "vc_123",
            idempotency_key="idem_123",
        )

        assert route.called
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_123"
        assert isinstance(result, MutationResource)


@pytest.mark.asyncio
async def test_async_voice_mutations_hangup_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.mutations.hangup("vc_123")

        assert route.called
        assert isinstance(result, MutationResource)
        assert result.request_id == "req_123"


# --- mute ---
def test_voice_mutations_mute_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/mute").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.mute(
            "vc_123",
            leg_id="leg_456",
            on=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["leg_id"] == "leg_456"
        assert body["on"] is True
        assert isinstance(result, MutationResource)


def test_voice_mutations_unmute():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/mute").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.mute(
            "vc_123",
            leg_id="leg_456",
            on=False,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["on"] is False
        assert isinstance(result, MutationResource)


def test_voice_mutations_mute_with_idempotency_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/mute").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.mute(
            "vc_123",
            leg_id="leg_456",
            on=True,
            idempotency_key="idem_456",
        )

        assert route.called
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_456"
        assert isinstance(result, MutationResource)


@pytest.mark.asyncio
async def test_async_voice_mutations_mute_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/mute").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.mutations.mute("vc_123", leg_id="leg_456", on=True)

        assert route.called
        assert isinstance(result, MutationResource)


# --- dtmf ---
def test_voice_mutations_dtmf_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/dtmf").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.dtmf(
            "vc_123",
            digits="123",
            duration_ms=200,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["digits"] == "123"
        assert body["duration_ms"] == 200
        assert "leg_id" not in body
        assert isinstance(result, MutationResource)


def test_voice_mutations_dtmf_with_leg_id():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/dtmf").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.dtmf(
            "vc_123",
            digits="1234567890*#",
            leg_id="leg_456",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["digits"] == "1234567890*#"
        assert body["leg_id"] == "leg_456"
        assert isinstance(result, MutationResource)


def test_voice_mutations_dtmf_without_optional_duration():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/dtmf").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.dtmf("vc_123", digits="456")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["digits"] == "456"
        assert "duration_ms" not in body
        assert isinstance(result, MutationResource)


def test_voice_mutations_dtmf_with_idempotency_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/dtmf").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.dtmf(
            "vc_123",
            digits="789",
            idempotency_key="idem_dtmf",
        )

        assert route.called
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_dtmf"
        assert isinstance(result, MutationResource)


@pytest.mark.asyncio
async def test_async_voice_mutations_dtmf_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/dtmf").mock(
            return_value=httpx.Response(200, json=MUTATION_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.mutations.dtmf("vc_123", digits="321")

        assert route.called
        assert isinstance(result, MutationResource)


# --- play ---
def test_voice_mutations_play_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["media_url"] == "https://example.com/audio.mp3"
        assert "leg_id" not in body
        assert "loop" not in body
        assert isinstance(result, MutationResource)
        assert result.playback_id == "playback_123"


def test_voice_mutations_play_with_loop():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/ringback.mp3",
            loop=5,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["loop"] == 5
        assert isinstance(result, MutationResource)


def test_voice_mutations_play_with_leg_id():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
            leg_id="leg_456",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["leg_id"] == "leg_456"
        assert isinstance(result, MutationResource)


def test_voice_mutations_play_with_on_dtmf():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
            on_dtmf="continue",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["on_dtmf"] == "continue"
        assert isinstance(result, MutationResource)


def test_voice_mutations_play_returns_playback_id():
    """Verify play returns playback_id in response."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_WITH_MEDIA_URL)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
        )

        assert route.called
        assert isinstance(result, MutationResource)
        assert result.playback_id == "playback_456"
        assert result.request_id == "req_789"


def test_voice_mutations_play_with_all_options():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
            leg_id="leg_456",
            loop=2,
            on_dtmf="stop",
            idempotency_key="idem_play",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["media_url"] == "https://example.com/audio.mp3"
        assert body["leg_id"] == "leg_456"
        assert body["loop"] == 2
        assert body["on_dtmf"] == "stop"
        headers = route.calls.last.request.headers
        assert headers["Idempotency-Key"] == "idem_play"
        assert isinstance(result, MutationResource)


@pytest.mark.asyncio
async def test_async_voice_mutations_play_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json=PLAYBACK_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
        )

        assert route.called
        assert isinstance(result, MutationResource)
        assert result.playback_id == "playback_123"


# --- data envelope unwrapping ---
def test_voice_mutations_hangup_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/vc_123/hangup").mock(
            return_value=httpx.Response(200, json={"data": MUTATION_JSON})
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.hangup("vc_123")

        assert isinstance(result, MutationResource)
        assert result.request_id == "req_123"


def test_voice_mutations_play_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/vc_123/play").mock(
            return_value=httpx.Response(200, json={"data": PLAYBACK_JSON})
        )
        client = Client(api_key="test_api_key")

        result = client.voice.mutations.play(
            "vc_123",
            media_url="https://example.com/audio.mp3",
        )

        assert isinstance(result, MutationResource)
        assert result.playback_id == "playback_123"
