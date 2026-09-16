import httpx
import pytest

from teler import AsyncClient, Client, exceptions
from teler.resources.events import (AsyncEventResourceManager,
                                     EventResourceManager)
from teler.resources.recordings import (AsyncRecordingResourceManager,
                                         RecordingResourceManager)
from teler.resources.voice.voice import (AsyncVoiceResourceManager,
                                          VoiceResourceManager)

TEST_API_KEY = "TEST_API_KEY"


# Sync client
def test_client_init_sets_api_key_and_client_and_managers():
    client = Client(api_key=TEST_API_KEY)

    assert client.api_key == TEST_API_KEY
    assert isinstance(client.httpx_client, httpx.Client)
    assert isinstance(client.voice, VoiceResourceManager)
    assert isinstance(client.events, EventResourceManager)
    assert isinstance(client.recordings, RecordingResourceManager)


def test_client_init_missing_api_key_raises():
    with pytest.raises(exceptions.BadParametersException) as exc:
        Client()

    assert exc.value.param == "api_key"
    assert "api_key is required" in str(exc.value)


def test_client_context_manager():
    with Client(api_key=TEST_API_KEY) as client:
        assert client.api_key == TEST_API_KEY
        assert isinstance(client.httpx_client, httpx.Client)
        assert isinstance(client.voice, VoiceResourceManager)
    # After context, the client should be closed
    assert client.httpx_client.is_closed


# Async client
@pytest.mark.asyncio
async def test_async_client_init_sets_api_key_and_client_and_managers():
    client = AsyncClient(api_key=TEST_API_KEY)

    assert client.api_key == TEST_API_KEY
    assert isinstance(client.httpx_client, httpx.AsyncClient)
    assert isinstance(client.voice, AsyncVoiceResourceManager)
    assert isinstance(client.events, AsyncEventResourceManager)
    assert isinstance(client.recordings, AsyncRecordingResourceManager)

    await client.httpx_client.aclose()


@pytest.mark.asyncio
async def test_async_client_init_missing_api_key_raises():
    with pytest.raises(exceptions.BadParametersException) as exc:
        AsyncClient()

    assert exc.value.param == "api_key"
    assert "api_key is required" in str(exc.value)


@pytest.mark.asyncio
async def test_async_client_context_manager():
    async with AsyncClient(api_key=TEST_API_KEY) as client:
        assert client.api_key == TEST_API_KEY
        assert isinstance(client.httpx_client, httpx.AsyncClient)
        assert isinstance(client.voice, AsyncVoiceResourceManager)
    # After context, the client should be closed
    assert client.httpx_client.is_closed


# Header merge precedence
def test_client_headers_override_sdk_defaults():
    client = Client(
        api_key=TEST_API_KEY, headers={"User-Agent": "my-app/1.0"}
    )

    assert client.httpx_client.headers["user-agent"] == "my-app/1.0"


def test_client_headers_override_is_case_insensitive():
    """A lowercase key must beat the TitleCase default, not sit beside it."""
    client = Client(
        api_key=TEST_API_KEY, headers={"user-agent": "my-app/1.0"}
    )

    assert client.httpx_client.headers["user-agent"] == "my-app/1.0"


def test_client_headers_cannot_displace_the_api_key():
    client = Client(api_key=TEST_API_KEY, headers={"X-Api-Key": "evil"})

    assert client.httpx_client.headers["x-api-key"] == TEST_API_KEY


def test_client_passes_through_unrelated_headers():
    client = Client(api_key=TEST_API_KEY, headers={"X-Trace-Id": "t1"})

    assert client.httpx_client.headers["x-trace-id"] == "t1"


def test_client_applies_defaults_when_no_headers_given():
    client = Client(api_key=TEST_API_KEY)
    headers = client.httpx_client.headers

    assert headers["content-type"] == "application/json"
    assert headers["accept"] == "application/json"
    assert headers["user-agent"].startswith("teler/")
    assert headers["x-api-key"] == TEST_API_KEY


@pytest.mark.asyncio
async def test_async_client_headers_override_sdk_defaults():
    client = AsyncClient(
        api_key=TEST_API_KEY, headers={"user-agent": "my-app/1.0"}
    )

    assert client.httpx_client.headers["user-agent"] == "my-app/1.0"

    await client.httpx_client.aclose()


@pytest.mark.asyncio
async def test_async_client_headers_cannot_displace_the_api_key():
    client = AsyncClient(api_key=TEST_API_KEY, headers={"X-Api-Key": "evil"})

    assert client.httpx_client.headers["x-api-key"] == TEST_API_KEY

    await client.httpx_client.aclose()


@pytest.mark.asyncio
async def test_async_client_applies_defaults_when_no_headers_given():
    client = AsyncClient(api_key=TEST_API_KEY)
    headers = client.httpx_client.headers

    assert headers["accept"] == "application/json"
    assert headers["user-agent"].startswith("teler/")

    await client.httpx_client.aclose()
