import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.voice.types import VoiceAppResource, DeleteResult
from teler.resources.virtual_numbers import VirtualNumberResource

BASE = "https://api.frejun.ai/api/v1"

APP_JSON = {
    "id": "va_123",
    "name": "Customer Support",
    "flow_url": "https://example.com/flow",
    "webhook_url": "https://example.com/webhook",
    "fallback_url": None,
    "status": "active",
    "channel_limit": 10,
    "vn_count": 2,
    "secret_id": None,
    "secret_name": None,
    "webhook_api_version": "2026-06-01",
    "account_id": "acc_1",
    "code": None,
}

LIST_JSON = {
    "data": [APP_JSON],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}

VN_JSON = {
    "id": "vn_123",
    "account_id": "acc_1",
    "name": "Support Line",
    "number": "+15550001111",
    "location": {"id": "loc_1", "name": "New York", "region_code": "NY", "country_code": "US"},
    "voice_app": {"id": "va_123", "name": "Customer Support"},
    "sip_trunk": None,
}

VN_LIST_JSON = {
    "data": [VN_JSON],
    "next_cursor": None,
    "previous_cursor": None,
    "has_more": False,
}


# --- create ---
def test_voice_apps_create_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(201, json=APP_JSON)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.create(
            name="Customer Support",
            flow_url="https://example.com/flow",
            webhook_url="https://example.com/webhook",
            channel_limit=10,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["name"] == "Customer Support"
        assert body["flow_url"] == "https://example.com/flow"
        assert body["webhook_url"] == "https://example.com/webhook"
        assert body["channel_limit"] == 10
        assert "fallback_url" not in body
        assert "vn_ids" not in body
        assert isinstance(app, VoiceAppResource)
        assert app.id == "va_123"
        assert app.status == "active"


def test_voice_apps_create_with_optional_fields():
    app_json = {
        **APP_JSON,
        "fallback_url": "https://example.com/fallback",
        "secret_id": "sec_123",
    }
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(201, json=app_json)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.create(
            name="Secure App",
            flow_url="https://example.com/flow",
            webhook_url="https://example.com/webhook",
            fallback_url="https://example.com/fallback",
            secret_id="sec_123",
            webhook_api_version="2026-06-01",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["fallback_url"] == "https://example.com/fallback"
        assert body["secret_id"] == "sec_123"
        assert body["webhook_api_version"] == "2026-06-01"
        assert isinstance(app, VoiceAppResource)


def test_voice_apps_create_with_vn_ids():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(201, json=APP_JSON)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.create(
            name="Customer Support",
            flow_url="https://example.com/flow",
            webhook_url="https://example.com/webhook",
            vn_ids=["vn_123", "vn_456"],
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["vn_ids"] == ["vn_123", "vn_456"]
        assert isinstance(app, VoiceAppResource)


@pytest.mark.asyncio
async def test_async_voice_apps_create_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(201, json=APP_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        app = await client.voice.apps.create(
            name="Customer Support",
            flow_url="https://example.com/flow",
            webhook_url="https://example.com/webhook",
            channel_limit=10,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["name"] == "Customer Support"
        assert isinstance(app, VoiceAppResource)
        assert app.id == "va_123"


# --- list ---
def test_voice_apps_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list(search="Customer", status="active", limit=20)

        assert route.called
        params = route.calls.last.request.url.params
        assert params["search"] == "Customer"
        assert params["status"] == "active"
        assert params["limit"] == "20"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], VoiceAppResource)
        assert page.data[0].id == "va_123"
        assert page.data[0].name == "Customer Support"


def test_voice_apps_list_with_cursor_pagination():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list(cursor_after="cur_next")

        assert route.called
        params = route.calls.last.request.url.params
        assert params["cursor_after"] == "cur_next"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VoiceAppResource)


def test_voice_apps_list_defaults_to_limit_50():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list()

        assert route.called
        params = route.calls.last.request.url.params
        assert params["limit"] == "50"
        assert isinstance(page, CursorPage)


@pytest.mark.asyncio
async def test_async_voice_apps_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.voice.apps.list(search="Customer")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VoiceAppResource)
        assert page.data[0].name == "Customer Support"


# --- retrieve ---
def test_voice_apps_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=APP_JSON)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.retrieve("va_123")

        assert route.called
        assert isinstance(app, VoiceAppResource)
        assert app.id == "va_123"
        assert app.name == "Customer Support"
        assert app.channel_limit == 10


def test_voice_apps_retrieve_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json={"data": APP_JSON})
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.retrieve("va_123")

        assert isinstance(app, VoiceAppResource)
        assert app.id == "va_123"
        assert app.status == "active"


@pytest.mark.asyncio
async def test_async_voice_apps_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=APP_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        app = await client.voice.apps.retrieve("va_123")

        assert route.called
        assert isinstance(app, VoiceAppResource)
        assert app.id == "va_123"


# --- update ---
def test_voice_apps_update_sends_payload_and_returns_resource():
    updated = {**APP_JSON, "name": "Updated App", "status": "inactive"}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.update("va_123", name="Updated App", status="inactive")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "Updated App", "status": "inactive"}
        assert isinstance(app, VoiceAppResource)
        assert app.name == "Updated App"
        assert app.status == "inactive"


def test_voice_apps_update_single_field():
    updated = {**APP_JSON, "channel_limit": 20}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.update("va_123", channel_limit=20)

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"channel_limit": 20}
        assert isinstance(app, VoiceAppResource)
        assert app.channel_limit == 20


def test_voice_apps_update_with_webhook():
    updated = {**APP_JSON, "webhook_url": "https://example.com/new-webhook"}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = Client(api_key="test_api_key")

        app = client.voice.apps.update(
            "va_123", webhook_url="https://example.com/new-webhook"
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"webhook_url": "https://example.com/new-webhook"}
        assert isinstance(app, VoiceAppResource)


@pytest.mark.asyncio
async def test_async_voice_apps_update_returns_resource():
    updated = {**APP_JSON, "name": "Async Updated"}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = AsyncClient(api_key="test_api_key")

        app = await client.voice.apps.update("va_123", name="Async Updated")

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "Async Updated"}
        assert isinstance(app, VoiceAppResource)
        assert app.name == "Async Updated"


# --- delete ---
def test_voice_apps_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "Voice app deleted."}
            )
        )
        client = Client(api_key="test_api_key")

        result = client.voice.apps.delete("va_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


@pytest.mark.asyncio
async def test_async_voice_apps_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/voice/apps/va_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "Voice app deleted."}
            )
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.voice.apps.delete("va_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


# --- list virtual numbers ---
def test_voice_apps_list_virtual_numbers_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list_virtual_numbers("va_123", search="Support")

        assert route.called
        assert route.calls.last.request.url.params["search"] == "Support"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)
        assert page.data[0].id == "vn_123"
        assert page.data[0].number == "+15550001111"


def test_voice_apps_list_virtual_numbers_with_location_filter():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list_virtual_numbers(
            "va_123", location=["loc_ny"]
        )

        assert route.called
        assert route.calls.last.request.url.params["location"] == "loc_ny"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)


def test_voice_apps_list_virtual_numbers_with_limit_50():
    """Virtual numbers endpoint has a max limit of 50, not 100."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.voice.apps.list_virtual_numbers("va_123", limit=50)

        assert route.called
        params = route.calls.last.request.url.params
        assert params["limit"] == "50"
        assert isinstance(page, CursorPage)


@pytest.mark.asyncio
async def test_async_voice_apps_list_virtual_numbers_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/voice/apps/va_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.voice.apps.list_virtual_numbers("va_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)
        assert page.data[0].voice_app["id"] == "va_123"
