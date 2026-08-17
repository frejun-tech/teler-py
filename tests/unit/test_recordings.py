import httpx
import pytest
import respx

from teler import AsyncClient, Client, exceptions
from teler.resources.recordings import RecordingResource

BASE = "https://api.frejun.ai/api/v1"
SIGNED_URL = "https://storage.example.com/rec_123.mp3?sig=abc"


def test_recordings_retrieve_returns_signed_url():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/recordings").mock(
            return_value=httpx.Response(302, headers={"location": SIGNED_URL})
        )
        client = Client(api_key="test_api_key")

        rec = client.recordings.retrieve("rec_123", expires_in=900)

        assert route.called
        assert route.calls.last.request.url.params["recording_id"] == "rec_123"
        assert isinstance(rec, RecordingResource)
        assert rec.url == SIGNED_URL
        assert rec.recording_id == "rec_123"
        assert rec.expires_in == 900


def test_recordings_retrieve_accepts_json_body():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/recordings").mock(
            return_value=httpx.Response(
                200, json={"url": SIGNED_URL, "expires_in": 600}
            )
        )
        client = Client(api_key="test_api_key")

        rec = client.recordings.retrieve("rec_123", expires_in=900)

        assert isinstance(rec, RecordingResource)
        assert rec.url == SIGNED_URL
        assert rec.expires_in == 600


@pytest.mark.asyncio
async def test_async_recordings_retrieve_returns_signed_url():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/recordings").mock(
            return_value=httpx.Response(302, headers={"location": SIGNED_URL})
        )
        client = AsyncClient(api_key="test_api_key")

        rec = await client.recordings.retrieve("rec_123")

        assert route.called
        assert isinstance(rec, RecordingResource)
        assert rec.url == SIGNED_URL


def test_recordings_request_path_has_no_trailing_slash():
    """A trailing slash makes the API 307-redirect to itself, so the SDK would
    return the API URL instead of the signed URL."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/recordings").mock(
            return_value=httpx.Response(307, headers={"location": SIGNED_URL})
        )
        client = Client(api_key="test_api_key")

        rec = client.recordings.retrieve("rec_123")

        assert route.called
        assert route.calls.last.request.url.path == "/api/v1/recordings"
        assert rec.url == SIGNED_URL


def test_recordings_retrieve_missing_id_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.recordings.retrieve("")


@pytest.mark.asyncio
async def test_async_recordings_retrieve_missing_id_raises():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.recordings.retrieve("")
