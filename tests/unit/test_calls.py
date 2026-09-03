import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.voice.types import CallLegResource, CreateCallResource

BASE = "https://api.frejun.ai/api/v1"


def test_call_create_hits_route_and_returns_call_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json={"id": "call_456"})
        )
        client = Client(api_key="test_api_key")
        data = {
            "from_number": "+123456789",
            "to_number": "+123456789",
            "flow_url": "https://api.frejun.ai/flow",
            "status_callback_url": "https://api.frejun.ai/status",
            "record": True,
        }

        call = client.voice.calls.create(**data)

        assert route.called
        assert isinstance(call, CreateCallResource)


@pytest.mark.asyncio
async def test_async_call_create_hits_route_and_returns_call_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json={"id": "call_456"})
        )
        client = AsyncClient(api_key="test_api_key")
        data = {
            "from_number": "+123456789",
            "to_number": "+987654321",
            "flow_url": "https://api.frejun.ai/flow",
            "status_callback_url": "https://api.frejun.ai/status",
            "record": True,
        }

        call = await client.voice.calls.create(**data)

        assert route.called
        assert isinstance(call, CreateCallResource)


LEGS_JSON = {
    "data": [
        {
            "id": "cl_1",
            "call_session_id": "call_123",
            "direction": "outbound",
            "role": "callee",
            "state": "ended",
            "from_number": "+123456789",
            "to_number": "+987654321",
            "parent_leg_id": None,
            "recordings": [],
            "created_at": "2026-08-01T12:00:00Z",
            "answered_at": None,
            "ended_at": None,
            "reason": None,
            "ended_by": None,
        }
    ],
    "next_cursor": None,
    "previous_cursor": None,
    "has_more": False,
}


def test_call_list_legs_returns_cursor_page_of_legs():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/call_123/legs").mock(
            return_value=httpx.Response(200, json=LEGS_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list_legs("call_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallLegResource)
        assert page.data[0].id == "cl_1"
        assert page.has_more is False


@pytest.mark.asyncio
async def test_async_call_list_legs_returns_cursor_page_of_legs():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/call_123/legs").mock(
            return_value=httpx.Response(200, json=LEGS_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.voice.calls.list_legs("call_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallLegResource)
