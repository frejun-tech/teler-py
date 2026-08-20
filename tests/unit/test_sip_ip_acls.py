import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client, exceptions
from teler.resources.base import CursorPage
from teler.resources.sip.ip_acls import MAX_ENTRIES_PER_IP_ACL
from teler.resources.sip.types import DeleteResult, IpAclResource

BASE = "https://api.frejun.ai/api/v1"

ACL_JSON = {
    "id": "acl_01JQ8Z9K7M3N2P4R5S6T7V8WST",
    "name": "carrier-egress",
    "addresses": [
        {"address": "203.0.113.7", "description": "primary PoP"},
        {"address": "198.51.100.0/24", "description": None},
    ],
    "trunk_count": 2,
    "created_at": "2026-08-01T12:00:00Z",
    "updated_at": "2026-08-02T09:30:00Z",
}

LIST_JSON = {
    "data": [
        {
            "id": "acl_01JQ8Z9K7M3N2P4R5S6T7V8WST",
            "name": "carrier-egress",
            "address_count": 2,
            "trunk_count": 2,
            "created_at": "2026-08-01T12:00:00Z",
        }
    ],
    "next_cursor": "cur_next",
    "previous_cursor": None,
    "has_more": True,
}

ADDRESSES = [{"address": "203.0.113.7", "description": "primary PoP"}]


# --- create ---
def test_create_sends_payload_and_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(201, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        acl = client.sip.ip_acls.create(name="carrier-egress", addresses=ADDRESSES)

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "carrier-egress", "addresses": ADDRESSES}
        assert isinstance(acl, IpAclResource)
        assert acl.id == "acl_01JQ8Z9K7M3N2P4R5S6T7V8WST"
        assert acl.trunk_count == 2
        assert acl.addresses[1]["address"] == "198.51.100.0/24"
        # only the list endpoint sends this
        assert acl.address_count is None


@pytest.mark.asyncio
async def test_async_create_returns_resource():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(201, json=ACL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        acl = await client.sip.ip_acls.create(
            name="carrier-egress", addresses=ADDRESSES
        )

        assert route.called
        assert isinstance(acl, IpAclResource)
        assert acl.name == "carrier-egress"


# --- list ---
def test_list_returns_cursor_page_and_sends_filters():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        page = client.sip.ip_acls.list(search="carrier", limit=25)

        assert route.called
        params = route.calls.last.request.url.params
        assert params["search"] == "carrier"
        assert params["limit"] == "25"
        assert isinstance(page, CursorPage)
        assert page.has_more is True
        assert page.next_cursor == "cur_next"
        item = page.data[0]
        assert isinstance(item, IpAclResource)
        assert item.address_count == 2
        # the list shape carries neither of these
        assert item.addresses is None
        assert item.updated_at is None


def test_list_default_limit_is_fifty():
    """The API defaults this endpoint to 50, unlike the SDK's other lists."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        client.sip.ip_acls.list()

        assert route.calls.last.request.url.params["limit"] == "50"


@pytest.mark.asyncio
async def test_async_list_returns_cursor_page():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        page = await client.sip.ip_acls.list()

        assert isinstance(page, CursorPage)
        assert len(page.data) == 1


# --- retrieve ---
def test_retrieve_requests_the_id_path():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        acl = client.sip.ip_acls.retrieve("acl_123")

        assert route.called
        assert isinstance(acl, IpAclResource)
        assert len(acl.addresses) == 2


@pytest.mark.asyncio
async def test_async_retrieve_requests_the_id_path():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        acl = await client.sip.ip_acls.retrieve("acl_123")

        assert route.called
        assert acl.id == "acl_01JQ8Z9K7M3N2P4R5S6T7V8WST"


# --- update ---
def test_update_sends_only_supplied_fields():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        client.sip.ip_acls.update("acl_123", name="renamed")

        body = json.loads(route.calls.last.request.content)
        assert body == {"name": "renamed"}


def test_update_can_replace_the_address_set():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        client.sip.ip_acls.update("acl_123", addresses=ADDRESSES)

        body = json.loads(route.calls.last.request.content)
        assert body == {"addresses": ADDRESSES}


@pytest.mark.asyncio
async def test_async_update_sends_payload():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = AsyncClient(api_key="test_api_key")

        await client.sip.ip_acls.update("acl_123", name="renamed")

        assert json.loads(route.calls.last.request.content) == {"name": "renamed"}


# --- delete ---
def test_delete_returns_delete_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.delete(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "message": "IP access control list deleted successfully.",
                },
            )
        )
        client = Client(api_key="test_api_key")

        result = client.sip.ip_acls.delete("acl_123")

        assert route.called
        assert isinstance(result, DeleteResult)
        assert result.success is True


def test_delete_while_attached_raises_conflict():
    """The API refuses with 409 while trunks still authorise against the ACL."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.delete(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(
                409,
                json={
                    "error": {
                        "type": "conflict",
                        "code": "acl_attached",
                        "message": "'carrier-egress' is attached to 2 trunk(s).",
                    }
                },
            )
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.ConflictException):
            client.sip.ip_acls.delete("acl_123")


@pytest.mark.asyncio
async def test_async_delete_returns_delete_result():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.delete(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(
                200, json={"success": True, "message": "deleted"}
            )
        )
        client = AsyncClient(api_key="test_api_key")

        result = await client.sip.ip_acls.delete("acl_123")

        assert result.success is True


# ---------------------------------------------------------------------------
# Client-side validation
#
# None of these rules appear in the OpenAPI schema; they come from the backend's
# IpAclCreate/IpAclUpdate models. Each asserts no request is sent, since the
# point is to fail before the round-trip.
# ---------------------------------------------------------------------------

def _unreachable_client(respx_mock):
    respx_mock.post(f"{BASE}/sip/ip-acls").mock(
        return_value=httpx.Response(201, json=ACL_JSON)
    )
    return Client(api_key="test_api_key")


def test_create_rejects_blank_name():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(name="   ", addresses=ADDRESSES)

        assert exc.value.param == "name"


def test_create_rejects_overlong_name():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.create(name="x" * 65, addresses=ADDRESSES)


def test_create_rejects_empty_address_list():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(name="acl", addresses=[])

        assert exc.value.param == "addresses"


def test_create_rejects_more_than_the_entry_cap():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)
        too_many = [
            {"address": f"203.0.113.{i}"} for i in range(MAX_ENTRIES_PER_IP_ACL + 1)
        ]

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(name="acl", addresses=too_many)

        assert "at most 50" in str(exc.value)


def test_create_accepts_exactly_the_entry_cap():
    """The cap is inclusive, so 50 entries must go through."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(201, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")
        exactly = [
            {"address": f"203.0.113.{i}"} for i in range(MAX_ENTRIES_PER_IP_ACL)
        ]

        client.sip.ip_acls.create(name="acl", addresses=exactly)

        assert route.called


def test_create_rejects_a_malformed_address():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(
                name="acl", addresses=[{"address": "not-an-ip"}]
            )

        assert "not a valid" in str(exc.value)


def test_create_rejects_an_out_of_range_octet():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.create(
                name="acl", addresses=[{"address": "203.0.113.999"}]
            )


def test_create_accepts_ipv6_and_cidr():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(201, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        client.sip.ip_acls.create(
            name="acl",
            addresses=[
                {"address": "2001:db8::1"},
                {"address": "2001:db8::/32"},
                {"address": "198.51.100.0/24"},
            ],
        )

        assert route.called


def test_create_rejects_exact_duplicate_addresses():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(
                name="acl",
                addresses=[{"address": "203.0.113.7"}, {"address": "203.0.113.7"}],
            )

        assert "Duplicate" in str(exc.value)


def test_create_rejects_duplicates_that_only_collide_once_canonicalised():
    """The API strips host bits, so these two are the same network."""
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(
                name="acl",
                addresses=[
                    {"address": "203.0.113.0/24"},
                    {"address": "203.0.113.7/24"},
                ],
            )

        assert "same network" in str(exc.value)


def test_create_rejects_an_overlong_description():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.create(
                name="acl",
                addresses=[{"address": "203.0.113.7", "description": "x" * 256}],
            )


def test_create_rejects_an_entry_missing_the_address_key():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.create(
                name="acl", addresses=[{"description": "no address"}]
            )


def test_update_allows_omitting_both_fields():
    """Both are optional on update, so neither may be demanded."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        client.sip.ip_acls.update("acl_123")

        assert json.loads(route.calls.last.request.content) == {}


def test_update_still_validates_supplied_addresses():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.update("acl_123", addresses=[{"address": "bad"}])


def test_update_rejects_an_empty_address_list():
    """``minItems: 1`` applies to update too, where None means 'leave alone'."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.patch(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json=ACL_JSON)
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.update("acl_123", addresses=[])


def test_create_rejects_an_explicit_none_name():
    """Required positionally, but nothing stops a caller passing None."""
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(name=None, addresses=ADDRESSES)

        assert exc.value.param == "name"


def test_create_rejects_an_explicit_none_address_list():
    with respx.mock(assert_all_called=False) as respx_mock:
        client = _unreachable_client(respx_mock)

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.create(name="acl", addresses=None)

        assert exc.value.param == "addresses"


def test_a_data_wrapped_response_is_unwrapped():
    """Detail responses may arrive inside a ``{"data": {...}}`` envelope."""
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/ip-acls/acl_123").mock(
            return_value=httpx.Response(200, json={"data": ACL_JSON})
        )
        client = Client(api_key="test_api_key")

        acl = client.sip.ip_acls.retrieve("acl_123")

        assert acl.id == "acl_01JQ8Z9K7M3N2P4R5S6T7V8WST"
        assert acl.trunk_count == 2


@pytest.mark.parametrize("limit", [0, 101])
def test_list_rejects_out_of_range_limits(limit):
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException) as exc:
            client.sip.ip_acls.list(limit=limit)

        assert exc.value.param == "limit"


def test_list_rejects_both_cursors():
    with respx.mock(assert_all_called=False) as respx_mock:
        respx_mock.get(f"{BASE}/sip/ip-acls").mock(
            return_value=httpx.Response(200, json=LIST_JSON)
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.sip.ip_acls.list(cursor_after="a", cursor_before="b")
