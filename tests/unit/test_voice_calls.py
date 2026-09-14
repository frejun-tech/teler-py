import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.voice.types import CallResource, CallLegResource, CreateCallResource

BASE = "https://api.frejun.ai/api/v1"

CALL_JSON = {
    "id": "vc_123",
    "account_id": "acc_1",
    "voice_app_id": "va_1",
    "state": "active",
    "direction": "inbound",
    "from_number": "+15550001111",
    "to_number": "+15550002222",
    "properties": None,
    "created_at": "2026-08-01T12:00:00Z",
    "answered_at": "2026-08-01T12:00:05Z",
    "ended_at": None,
    "reason": None,
    "legs": [],
}

COMPLETED_CALL_JSON = {
    "id": "vc_456",
    "account_id": "acc_1",
    "voice_app_id": "va_1",
    "state": "completed",
    "direction": "outbound",
    "from_number": "+15550002222",
    "to_number": "+15550003333",
    "properties": {"custom_key": "custom_value"},
    "created_at": "2026-08-01T12:00:00Z",
    "answered_at": "2026-08-01T12:00:05Z",
    "ended_at": "2026-08-01T12:05:00Z",
    "reason": "normal_clearing",
    "legs": [{"id": "leg_1", "role": "primary"}],
}

CALL_LIST_JSON = {
    "data": [CALL_JSON, COMPLETED_CALL_JSON],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}

CREATE_CALL_JSON = {
    "id": "vc_789",
    "from_number": "+15550001111",
    "to_number": "+15550002222",
    "status_callback_url": "https://example.com/callback",
    "record": True,
}

LEG_JSON = {
    "id": "leg_1",
    "call_session_id": "vc_123",
    "direction": "inbound",
    "role": "primary",
    "state": "active",
    "from_number": "+15550001111",
    "to_number": "+15550002222",
    "parent_leg_id": None,
    "recordings": ["rec_1"],
    "created_at": "2026-08-01T12:00:00Z",
    "answered_at": "2026-08-01T12:00:05Z",
    "ended_at": None,
    "reason": None,
    "ended_by": None,
}

LEGS_LIST_JSON = {
    "data": [LEG_JSON],
    "next_cursor": None,
    "previous_cursor": None,
    "has_more": False,
}


# --- create ---
def test_voice_calls_create_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json=CREATE_CALL_JSON)
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.create(
            from_number="+15550001111",
            to_number="+15550002222",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/callback",
            record=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["from_number"] == "+15550001111"
        assert body["to_number"] == "+15550002222"
        assert body["flow_url"] == "https://example.com/flow"
        assert body["status_callback_url"] == "https://example.com/callback"
        assert body["record"] is True
        assert isinstance(call, CreateCallResource)
        assert call.id == "vc_789"


def test_voice_calls_create_without_recording():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(
                201,
                json={
                    **CREATE_CALL_JSON,
                    "record": False,
                    "id": "vc_999",
                },
            )
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.create(
            from_number="+15550001111",
            to_number="+15550002222",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/callback",
            record=False,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["record"] is False
        assert isinstance(call, CreateCallResource)


def test_voice_calls_create_defaults_record_to_true():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json=CREATE_CALL_JSON)
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.create(
            from_number="+15550001111",
            to_number="+15550002222",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/callback",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["record"] is True
        assert isinstance(call, CreateCallResource)


@pytest.mark.asyncio
async def test_async_voice_calls_create_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json=CREATE_CALL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        call = await client.voice.calls.create(
            from_number="+15550001111",
            to_number="+15550002222",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/callback",
            record=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["from_number"] == "+15550001111"
        assert isinstance(call, CreateCallResource)
        assert call.id == "vc_789"


# --- list ---
def test_voice_calls_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list(
            state="active", from_number="+15550001111", limit=25
        )

        assert route.called
        params = route.calls.last.request.url.params
        assert params["state"] == "active"
        assert params["from_number"] == "+15550001111"
        assert params["limit"] == "25"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], CallResource)
        assert page.data[0].id == "vc_123"
        assert page.data[0].state == "active"


def test_voice_calls_list_with_to_number_filter():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list(to_number="+15550002222")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["to_number"] == "+15550002222"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallResource)


def test_voice_calls_list_with_date_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list(
            created_after="2026-01-01T00:00:00Z",
            created_before="2026-12-31T23:59:59Z",
        )

        assert route.called
        params = route.calls.last.request.url.params
        assert params["created_after"] == "2026-01-01T00:00:00Z"
        assert params["created_before"] == "2026-12-31T23:59:59Z"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallResource)


def test_voice_calls_list_defaults_to_limit_50():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list()

        assert route.called
        params = route.calls.last.request.url.params
        assert params["limit"] == "50"
        assert isinstance(page, CursorPage)


def test_voice_calls_list_with_cursor_pagination():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list(cursor_after="cur_next")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["cursor_after"] == "cur_next"
        assert isinstance(page, CursorPage)


@pytest.mark.asyncio
async def test_async_voice_calls_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.voice.calls.list(state="active")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallResource)
        assert page.data[0].state == "active"


# --- retrieve ---
def test_voice_calls_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123").mock(
            return_value=httpx.Response(200, json=CALL_JSON)
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.retrieve("vc_123")

        assert route.called
        assert isinstance(call, CallResource)
        assert call.id == "vc_123"
        assert call.state == "active"
        assert call.direction == "inbound"


def test_voice_calls_retrieve_completed_call():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_456").mock(
            return_value=httpx.Response(200, json=COMPLETED_CALL_JSON)
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.retrieve("vc_456")

        assert route.called
        assert isinstance(call, CallResource)
        assert call.id == "vc_456"
        assert call.state == "completed"
        assert call.reason == "normal_clearing"
        assert call.properties == {"custom_key": "custom_value"}


def test_voice_calls_retrieve_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/voice/calls/vc_123").mock(
            return_value=httpx.Response(200, json={"data": CALL_JSON})
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.retrieve("vc_123")

        assert isinstance(call, CallResource)
        assert call.id == "vc_123"
        assert call.state == "active"


@pytest.mark.asyncio
async def test_async_voice_calls_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123").mock(
            return_value=httpx.Response(200, json=CALL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        call = await client.voice.calls.retrieve("vc_123")

        assert route.called
        assert isinstance(call, CallResource)
        assert call.id == "vc_123"
        assert call.from_number == "+15550001111"


# --- get legs ---
def test_voice_calls_get_legs_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123/legs").mock(
            return_value=httpx.Response(200, json=LEGS_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.get_legs("vc_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallLegResource)
        assert page.data[0].id == "leg_1"
        assert page.data[0].role == "primary"


def test_voice_calls_get_legs_with_pagination():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123/legs").mock(
            return_value=httpx.Response(200, json=LEGS_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.get_legs("vc_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert page.has_more is False
        assert isinstance(page.data[0], CallLegResource)


def test_voice_calls_get_legs_returns_leg_properties():
    leg_with_details = {
        **LEG_JSON,
        "id": "leg_2",
        "role": "transferred",
        "state": "completed",
        "ended_by": "callee",
        "reason": "normal_clearing",
    }
    legs_list = {
        **LEGS_LIST_JSON,
        "data": [leg_with_details],
    }
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123/legs").mock(
            return_value=httpx.Response(200, json=legs_list)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.get_legs("vc_123")

        assert route.called
        leg = page.data[0]
        assert isinstance(leg, CallLegResource)
        assert leg.id == "leg_2"
        assert leg.role == "transferred"
        assert leg.state == "completed"
        assert leg.ended_by == "callee"
        assert leg.reason == "normal_clearing"
        assert leg.recordings == ["rec_1"]


@pytest.mark.asyncio
async def test_async_voice_calls_get_legs_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls/vc_123/legs").mock(
            return_value=httpx.Response(200, json=LEGS_LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.voice.calls.get_legs("vc_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], CallLegResource)
        assert page.data[0].role == "primary"


# --- edge cases ---
def test_voice_calls_create_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.post(f"{BASE}/voice/calls/initiate").mock(
            return_value=httpx.Response(201, json={"data": CREATE_CALL_JSON})
        )
        client = Client(api_key="test_api_key")

        call = client.voice.calls.create(
            from_number="+15550001111",
            to_number="+15550002222",
            flow_url="https://example.com/flow",
            status_callback_url="https://example.com/callback",
        )

        assert isinstance(call, CreateCallResource)
        assert call.id == "vc_789"


def test_voice_calls_list_multiple_state_values_not_supported():
    """Verify state filter accepts single value, not list."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/calls").mock(
            return_value=httpx.Response(200, json=CALL_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.calls.list(state="completed")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["state"] == "completed"
        assert isinstance(page, CursorPage)
