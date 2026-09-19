import httpx
import pytest
import respx

from teler import AsyncClient, Client
from teler.resources.base import CursorPage
from teler.resources.virtual_numbers import VirtualNumberResource, VNActionResult

BASE = "https://api.frejun.ai/api/v1"

VN_JSON = {
    "id": "vn_123",
    "account_id": "acc_1",
    "name": "Support Line",
    "number": "+15550001111",
    "location": {"id": "loc_1", "name": "New York", "region_code": "NY", "country_code": "US"},
    "voice_app": {"id": "app_1", "name": "Support App"},
    "sip_trunk": None,
}

LIST_JSON = {
    "data": [VN_JSON],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}

ACTION_JSON = {"success": True, "message": "2 virtual numbers assigned."}


# --- list ---
def test_virtual_numbers_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/virtual-numbers").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.virtual_numbers.list(search="Support", location=["loc_1"])

        assert route.called
        params = route.calls.last.request.url.params
        assert params["search"] == "Support"
        assert params["location"] == "loc_1"
        assert params["limit"] == "10"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        assert isinstance(page.data[0], VirtualNumberResource)
        assert page.data[0].id == "vn_123"
        assert page.data[0].number == "+15550001111"


@pytest.mark.asyncio
async def test_async_virtual_numbers_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/virtual-numbers").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.virtual_numbers.list(search="Support")

        assert route.called
        assert isinstance(page, CursorPage)
        assert isinstance(page.data[0], VirtualNumberResource)


# --- assign ---
def test_virtual_numbers_assign_sends_payload_and_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/assign").mock(
            return_value=httpx.Response(200, json=ACTION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.virtual_numbers.assign(
            vn_ids=["vn_123", "vn_456"], voice_app_id="app_1"
        )

        assert route.called
        import json

        body = json.loads(route.calls.last.request.content)
        assert body["vn_ids"] == ["vn_123", "vn_456"]
        assert body["voice_app_id"] == "app_1"
        assert body["apply_to_all"] is False
        assert "sip_trunk_id" not in body
        assert isinstance(result, VNActionResult)
        assert result.success is True


def test_virtual_numbers_assign_apply_to_all_sends_filter_params():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/assign").mock(
            return_value=httpx.Response(200, json=ACTION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.virtual_numbers.assign(
            apply_to_all=True, sip_trunk_id="st_1", search="Support"
        )

        assert route.called
        request = route.calls.last.request
        assert request.url.params["search"] == "Support"
        import json

        body = json.loads(request.content)
        assert body["apply_to_all"] is True
        assert body["sip_trunk_id"] == "st_1"
        assert isinstance(result, VNActionResult)


@pytest.mark.asyncio
async def test_async_virtual_numbers_assign_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/assign").mock(
            return_value=httpx.Response(200, json=ACTION_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.virtual_numbers.assign(
            vn_ids=["vn_123"], voice_app_id="app_1"
        )

        assert route.called
        assert isinstance(result, VNActionResult)
        assert result.success is True


# --- unassign ---
def test_virtual_numbers_unassign_sends_payload_and_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/unassign").mock(
            return_value=httpx.Response(200, json=ACTION_JSON)
        )
        client = Client(api_key="test_api_key")

        result = client.virtual_numbers.unassign(vn_ids=["vn_123"])

        assert route.called
        import json

        body = json.loads(route.calls.last.request.content)
        assert body["vn_ids"] == ["vn_123"]
        assert body["apply_to_all"] is False
        assert isinstance(result, VNActionResult)
        assert result.success is True


@pytest.mark.asyncio
async def test_async_virtual_numbers_unassign_returns_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/unassign").mock(
            return_value=httpx.Response(200, json=ACTION_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.virtual_numbers.unassign(apply_to_all=True)

        assert route.called
        assert isinstance(result, VNActionResult)


# --- update ---
def test_virtual_numbers_update_sends_payload_and_returns_resource():
    updated = {**VN_JSON, "name": "Renamed Line"}
    updated.pop("account_id")
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/virtual-numbers/vn_123").mock(
            return_value=httpx.Response(200, json=updated)
        )
        client = Client(api_key="test_api_key")

        vn = client.virtual_numbers.update("vn_123", name="Renamed Line")

        assert route.called
        import json

        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "Renamed Line"}
        assert isinstance(vn, VirtualNumberResource)
        assert vn.name == "Renamed Line"


def test_virtual_numbers_update_unwraps_data_envelope():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.patch(f"{BASE}/virtual-numbers/vn_123").mock(
            return_value=httpx.Response(200, json={"data": VN_JSON})
        )
        client = Client(api_key="test_api_key")

        vn = client.virtual_numbers.update("vn_123", name="Support Line")

        assert isinstance(vn, VirtualNumberResource)
        assert vn.id == "vn_123"


@pytest.mark.asyncio
async def test_async_virtual_numbers_update_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/virtual-numbers/vn_123").mock(
            return_value=httpx.Response(200, json=VN_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        vn = await client.virtual_numbers.update("vn_123", name="Support Line")

        assert route.called
        assert isinstance(vn, VirtualNumberResource)
        assert vn.id == "vn_123"
