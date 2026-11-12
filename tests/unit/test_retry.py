import asyncio
import time

import httpx
import pytest
import respx

from src.teler.constants import BASE_URL
from teler import AsyncClient, Client, exceptions

BASE = f"{BASE_URL}/api/v1"


def test_sync_retry_honours_retry_after_header(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events/evt_x").mock(
            side_effect=[
                httpx.Response(
                    429,
                    headers={"Retry-After": "2"},
                    json={"message": "slow down"},
                ),
                httpx.Response(200, json={"id": "evt_x"}),
            ]
        )
        client = Client(api_key="test_api_key")

        event = client.events.retrieve("evt_x")

    assert event.id == "evt_x"
    assert route.call_count == 2
    # The header wins over the exponential fallback.
    assert sleeps == [2.0]


def test_sync_retry_falls_back_to_exponential_delay(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/events/evt_x").mock(
            side_effect=[
                httpx.Response(503, json={"message": "unavailable"}),
                httpx.Response(200, json={"id": "evt_x"}),
            ]
        )
        client = Client(api_key="test_api_key")

        client.events.retrieve("evt_x")

    assert len(sleeps) == 1
    # GET uses a 100 ms base delay, so the jittered delay stays under it.
    assert 0.0 <= sleeps[0] < 0.1


def test_sync_client_does_not_retry_client_errors(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events/evt_x").mock(
            return_value=httpx.Response(400, json={"message": "bad"})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.events.retrieve("evt_x")

    assert route.call_count == 1
    assert sleeps == []


@pytest.mark.asyncio
async def test_async_retry_honours_retry_after_header(monkeypatch):
    sleeps = []

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events/evt_x").mock(
            side_effect=[
                httpx.Response(
                    429,
                    headers={"Retry-After": "2"},
                    json={"message": "slow down"},
                ),
                httpx.Response(200, json={"id": "evt_x"}),
            ]
        )
        client = AsyncClient(api_key="test_api_key")

        event = await client.events.retrieve("evt_x")
        await client.httpx_client.aclose()

    assert event.id == "evt_x"
    assert route.call_count == 2
    assert sleeps == [2.0]


def test_delete_is_not_retried_by_default(monkeypatch):
    """A retry after a lost response would report a successful delete as 404."""
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/secrets/sec_1").mock(
            side_effect=[
                httpx.Response(503, json={"message": "unavailable"}),
                httpx.Response(204),
            ]
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.TelerException):
            client.request("DELETE", f"{BASE}/secrets/sec_1")

    assert route.call_count == 1
    assert sleeps == []


def test_delete_retries_when_opted_in(monkeypatch):
    sleeps = []
    monkeypatch.setattr(time, "sleep", lambda seconds: sleeps.append(seconds))

    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/secrets/sec_1").mock(
            side_effect=[
                httpx.Response(503, json={"message": "unavailable"}),
                httpx.Response(204),
            ]
        )
        client = Client(api_key="test_api_key")

        client.request(
            "DELETE",
            f"{BASE}/secrets/sec_1",
            retry=True,
            base_retry_delay_ms=1,
        )

    assert route.call_count == 2
    assert len(sleeps) == 1


class _StubResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {}


def test_request_timeout_is_interpreted_as_milliseconds():
    client = Client(api_key="test_api_key")
    captured = {}

    def fake_request(*args, **kwargs):
        captured.update(kwargs)
        return _StubResponse()

    client.httpx_client.request = fake_request
    client.request("GET", f"{BASE}/events/evt_x", timeout=500)

    assert captured["timeout"] == 0.5


@pytest.mark.asyncio
async def test_async_request_timeout_is_interpreted_as_milliseconds():
    client = AsyncClient(api_key="test_api_key")
    captured = {}

    async def fake_request(*args, **kwargs):
        captured.update(kwargs)
        return _StubResponse()

    client.httpx_client.request = fake_request
    await client.request("GET", f"{BASE}/events/evt_x", timeout=500)

    assert captured["timeout"] == 0.5
