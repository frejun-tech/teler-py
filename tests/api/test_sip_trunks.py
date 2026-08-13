import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.sip.types import DeleteResult, SipTrunkResource
from teler.resources.virtual_numbers import VirtualNumberResource

BASE = "https://api.frejun.ai/api/v1"

TRUNK_JSON = {
    "id": "st_123",
    "name": "Main Trunk",
    "domain_name": "trunk.example.com",
    "account_id": "acc_1",
    "channel_limit": 10,
    "cps_limit": 5,
    "recording_enabled": True,
    "secure": False,
    "is_active": True,
    "auth_ip_addresses": ["10.0.0.1"],
    "auth_credential_usernames": ["sipuser"],
    "sip_route": {"name": "route-1", "sip_url": "sip.example.com"},
    "webhook_url": "https://example.com/webhook",
    "webhook_api_version": "2026-06-01",
    "created_at": "2026-08-01T12:00:00Z",
    "updated_at": None,
    "secret_id": "sec_1",
    "secret_name": "prod-secret",
}

LIST_JSON = {
    "data": [TRUNK_JSON],
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
    "voice_app": None,
    "sip_trunk": {"id": "st_123", "name": "Main Trunk"},
}

VN_LIST_JSON = {
    "data": [VN_JSON],
    "next_cursor": None,
    "previous_cursor": None,
    "has_more": False,
}


# --- create ---
def test_sip_trunks_create_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json=TRUNK_JSON)
        )
        client = Client(api_key="test_api_key")

        trunk = client.sip.trunks.create(
            name="Main Trunk",
            domain_name="trunk.example.com",
            authentication_type="credential",
            auth_credential={"username": "sipuser", "password": "sippass"},
            channel_limit=10,
            recording=True,
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["name"] == "Main Trunk"
        assert body["domain_name"] == "trunk.example.com"
        assert body["authentication_type"] == "credential"
        assert body["auth_credential"] == {"username": "sipuser", "password": "sippass"}
        assert body["channel_limit"] == 10
        assert body["recording"] is True
        assert "webhook_url" not in body
        assert isinstance(trunk, SipTrunkResource)
        assert trunk.id == "st_123"


@pytest.mark.asyncio
async def test_async_sip_trunks_create_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json=TRUNK_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        trunk = await client.sip.trunks.create(
            name="Main Trunk",
            domain_name="trunk.example.com",
            authentication_type="IP",
            auth_addresses=[{"name": "gw-1", "address": "10.0.0.1"}],
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["authentication_type"] == "IP"
        assert body["auth_addresses"] == [{"name": "gw-1", "address": "10.0.0.1"}]
        assert isinstance(trunk, SipTrunkResource)


# --- list ---
def test_sip_trunks_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.sip.trunks.list(search="Main", status=["active"])

        assert route.called
        params = route.calls.last.request.url.params
        assert params["search"] == "Main"
        assert params["status"] == "active"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert isinstance(page.data[0], SipTrunkResource)
        assert page.data[0].domain_name == "trunk.example.com"


@pytest.mark.asyncio
async def test_async_sip_trunks_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.sip.trunks.list()

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], SipTrunkResource)


# --- retrieve ---
def test_sip_trunks_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(200, json=TRUNK_JSON)
        )
        client = Client(api_key="test_api_key")

        trunk = client.sip.trunks.retrieve("st_123")

        assert route.called
        assert isinstance(trunk, SipTrunkResource)
        assert trunk.id == "st_123"
        assert trunk.cps_limit == 5


def test_sip_trunks_retrieve_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(200, json={"data": TRUNK_JSON})
        )
        client = Client(api_key="test_api_key")

        trunk = client.sip.trunks.retrieve("st_123")

        assert isinstance(trunk, SipTrunkResource)
        assert trunk.id == "st_123"


@pytest.mark.asyncio
async def test_async_sip_trunks_retrieve_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(200, json=TRUNK_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        trunk = await client.sip.trunks.retrieve("st_123")

        assert route.called
        assert isinstance(trunk, SipTrunkResource)


# --- update ---
def test_sip_trunks_update_sends_payload_and_returns_resource():
    updated = {**TRUNK_JSON, "name": "Renamed Trunk", "is_active": False}
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = Client(api_key="test_api_key")

        trunk = client.sip.trunks.update(
            "st_123", name="Renamed Trunk", is_active=False
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "Renamed Trunk", "is_active": False}
        assert isinstance(trunk, SipTrunkResource)
        assert trunk.name == "Renamed Trunk"


@pytest.mark.asyncio
async def test_async_sip_trunks_update_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(200, json=TRUNK_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        trunk = await client.sip.trunks.update("st_123", channel_limit=20)

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"channel_limit": 20}
        assert isinstance(trunk, SipTrunkResource)


# --- delete ---
def test_sip_trunks_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "SIP trunk deleted."}
            )
        )
        client = Client(api_key="test_api_key")

        result = client.sip.trunks.delete("st_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


@pytest.mark.asyncio
async def test_async_sip_trunks_delete_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/sip/trunks/st_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "SIP trunk deleted."}
            )
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.sip.trunks.delete("st_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


# --- list virtual numbers ---
def test_sip_trunks_list_virtual_numbers_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks/st_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.sip.trunks.list_virtual_numbers("st_123", search="Support")

        assert route.called
        assert route.calls.last.request.url.params["search"] == "Support"
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)
        assert page.data[0].id == "vn_123"


@pytest.mark.asyncio
async def test_async_sip_trunks_list_virtual_numbers_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/trunks/st_123/virtual-numbers").mock(
            return_value=httpx.Response(200, json=VN_LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.sip.trunks.list_virtual_numbers("st_123")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)
