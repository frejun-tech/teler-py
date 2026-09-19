import httpx
import pytest
import respx

from teler import AsyncClient, Client, exceptions

BASE = "https://api.frejun.ai/api/v1"


@pytest.mark.parametrize(
    "status,exc",
    [
        (400, exceptions.BadParametersException),
        (401, exceptions.UnauthorizedException),
        (403, exceptions.ForbiddenException),
        (404, exceptions.NotFoundException),
        (409, exceptions.ConflictException),
        (410, exceptions.GoneException),
        (422, exceptions.UnprocessableRequestException),
        (429, exceptions.RateLimitException),
        (500, exceptions.TelerException),
    ],
)
def test_request_maps_status_to_exception(status, exc):
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/events/evt_x").mock(
            return_value=httpx.Response(status, json={"detail": "nope"})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exc):
            client.events.retrieve("evt_x")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,exc",
    [
        (404, exceptions.NotFoundException),
        (410, exceptions.GoneException),
        (500, exceptions.TelerException),
    ],
)
async def test_async_request_maps_status_to_exception(status, exc):
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/events/evt_x").mock(
            return_value=httpx.Response(status, json={"detail": "nope"})
        )
        client = AsyncClient(api_key="test_api_key")

        with pytest.raises(exc):
            await client.events.retrieve("evt_x")

        await client.httpx_client.aclose()
