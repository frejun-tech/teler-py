import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.events import EventRedeliverResult, EventResource

BASE = "https://api.frejun.ai/api/v1"

EVENT_JSON = {
    "id": "evt_123",
    "account_id": "acc_1",
    "call_id": "call_1",
    "type": "call.completed",
    "occurred_at": "2026-07-07T12:00:00Z",
    "payload": {"foo": "bar"},
    "delivery_status": "delivered",
    "attempt_count": 1,
    "created_at": "2026-07-07T12:00:00Z",
}

LIST_JSON = {
    "data": [EVENT_JSON],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}


# --- list ---
def test_events_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.events.list(call_id="call_1")

        assert route.called
        assert route.calls.last.request.url.params["call_id"] == "call_1"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], EventResource)
        assert page.data[0].id == "evt_123"


@pytest.mark.asyncio
async def test_async_events_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.events.list(call_id="call_1")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], EventResource)


# --- retrieve ---
def test_events_retrieve_returns_event_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events/evt_123").mock(
            return_value=httpx.Response(200, json=EVENT_JSON)
        )
        client = Client(api_key="test_api_key")

        event = client.events.retrieve("evt_123")

        assert route.called
        assert isinstance(event, EventResource)
        assert event.id == "evt_123"
        assert event.delivery_status == "delivered"


@pytest.mark.asyncio
async def test_async_events_retrieve_returns_event_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events/evt_123").mock(
            return_value=httpx.Response(200, json=EVENT_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        event = await client.events.retrieve("evt_123")

        assert route.called
        assert isinstance(event, EventResource)
        assert event.id == "evt_123"


# --- redeliver ---
def test_events_redeliver_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/events/evt_123/redeliver").mock(
            return_value=httpx.Response(
                200, json={"event_id": "evt_123", "redelivered_at": "2026-07-07T13:00:00Z"}
            )
        )
        client = Client(api_key="test_api_key")

        result = client.events.redeliver("evt_123")

        assert route.called
        assert isinstance(result, EventRedeliverResult)
        assert result.event_id == "evt_123"
        assert result.redelivered_at == "2026-07-07T13:00:00Z"


@pytest.mark.asyncio
async def test_async_events_redeliver_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/events/evt_123/redeliver").mock(
            return_value=httpx.Response(
                200, json={"event_id": "evt_123", "redelivered_at": "2026-07-07T13:00:00Z"}
            )
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.events.redeliver("evt_123")

        assert route.called
        assert isinstance(result, EventRedeliverResult)
        assert result.event_id == "evt_123"
