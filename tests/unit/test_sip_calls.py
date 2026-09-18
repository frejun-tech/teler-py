import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.sip.types import SipCallResource

BASE = "https://api.frejun.ai/api/v1"

SIP_CALL_JSON = {
    "id": "cs_123",
    "account_id": "acc_1",
    "sip_trunk_id": "st_1",
    "state": "completed",
    "direction": "inbound",
    "from_number": "+15550001111",
    "to_number": "+15550002222",
    "created_at": "2026-08-01T12:00:00Z",
    "answered_at": "2026-08-01T12:00:05Z",
    "ended_at": "2026-08-01T12:05:00Z",
    "duration_seconds": 295,
    "reason": "normal_clearing",
    "ended_by": "callee",
    "recordings": ["rec_1"],
}

LIST_JSON = {
    "data": [SIP_CALL_JSON],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}


# --- list ---
def test_sip_calls_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/calls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.sip.calls.list(trunk_id="st_1", from_number="+15550001111")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["trunk_id"] == "st_1"
        assert params["from_number"] == "+15550001111"
        assert params["limit"] == "50"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], SipCallResource)
        assert page.data[0].id == "cs_123"
        assert page.data[0].duration_seconds == 295


@pytest.mark.asyncio
async def test_async_sip_calls_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/calls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.sip.calls.list(trunk_id="st_1")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], SipCallResource)


# --- retrieve ---
def test_sip_calls_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/calls/cs_123").mock(
            return_value=httpx.Response(200, json=SIP_CALL_JSON)
        )
        client = Client(api_key="test_api_key")

        call = client.sip.calls.retrieve("cs_123")

        assert route.called
        assert isinstance(call, SipCallResource)
        assert call.id == "cs_123"
        assert call.state == "completed"
        assert call.recordings == ["rec_1"]


def test_sip_calls_retrieve_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/calls/cs_123").mock(
            return_value=httpx.Response(200, json={"data": SIP_CALL_JSON})
        )
        client = Client(api_key="test_api_key")

        call = client.sip.calls.retrieve("cs_123")

        assert isinstance(call, SipCallResource)
        assert call.id == "cs_123"


@pytest.mark.asyncio
async def test_async_sip_calls_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/calls/cs_123").mock(
            return_value=httpx.Response(200, json=SIP_CALL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        call = await client.sip.calls.retrieve("cs_123")

        assert route.called
        assert isinstance(call, SipCallResource)
        assert call.id == "cs_123"
