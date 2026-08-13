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
    with pytest.raises(exceptions.BadParametersException):
        Client()


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
    with pytest.raises(exceptions.BadParametersException):
        AsyncClient()


@pytest.mark.asyncio
async def test_async_client_context_manager():
    async with AsyncClient(api_key=TEST_API_KEY) as client:
        assert client.api_key == TEST_API_KEY
        assert isinstance(client.httpx_client, httpx.AsyncClient)
        assert isinstance(client.voice, AsyncVoiceResourceManager)
    # After context, the client should be closed
    assert client.httpx_client.is_closed
