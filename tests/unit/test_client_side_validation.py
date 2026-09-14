"""Guards for API rules that the OpenAPI schema cannot express.

Each test asserts the SDK raises before any HTTP request is issued, so the rule
is enforced client-side rather than round-tripping to a server 422.
"""
import json

import httpx
import pytest
import respx

from teler import AsyncClient, Client, exceptions

BASE = "https://api.frejun.ai/api/v1"

CREDENTIAL = {"username": "sipuser", "password": "sippass"}
ADDRESS = {"name": "gw-1", "address": "10.0.0.1"}


# --- virtual number selection: vn_ids or apply_to_all ---
def test_vn_assign_without_selection_raises_before_request():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/assign").mock(
            return_value=httpx.Response(200, json={"success": True, "message": "ok"})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.virtual_numbers.assign(voice_app_id="app_1")

        assert not route.called


def test_vn_unassign_without_selection_raises_before_request():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/unassign").mock(
            return_value=httpx.Response(200, json={"success": True, "message": "ok"})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.virtual_numbers.unassign()

        assert not route.called


@pytest.mark.asyncio
async def test_async_vn_assign_without_selection_raises():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.virtual_numbers.assign(voice_app_id="app_1")


# --- virtual number assign target: exactly one of voice_app_id / sip_trunk_id ---
def test_vn_assign_without_target_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.virtual_numbers.assign(vn_ids=["vn_1"])


def test_vn_assign_with_both_targets_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.virtual_numbers.assign(
            vn_ids=["vn_1"], voice_app_id="app_1", sip_trunk_id="st_1"
        )


def test_vn_assign_with_apply_to_all_and_one_target_is_allowed():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/virtual-numbers/assign").mock(
            return_value=httpx.Response(200, json={"success": True, "message": "ok"})
        )
        client = Client(api_key="test_api_key")

        client.virtual_numbers.assign(apply_to_all=True, sip_trunk_id="st_1")

        assert route.called


# --- SIP trunk auth pairing ---
def test_trunk_credential_without_auth_credential_raises():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.sip.trunks.create(
                name="T", domain_name="t.example.com",
                authentication_type="credential",
            )

        assert not route.called


def test_trunk_credential_with_auth_addresses_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential",
            auth_credential=CREDENTIAL, auth_addresses=[ADDRESS],
        )


def test_trunk_ip_without_auth_addresses_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
        )


def test_trunk_rejects_more_than_five_auth_addresses():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS] * 6,
        )


def test_trunk_accepts_five_auth_addresses():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS] * 5,
        )

        assert route.called


def test_trunk_ip_accepts_an_ip_acl_id_instead_of_addresses():
    """An ACL is the other permitted auth source for ``IP``."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            ip_acl_id="acl_123",
        )

        assert route.called
        body = json.loads(route.calls.last.request.content)
        assert body["ip_acl_id"] == "acl_123"
        assert "auth_addresses" not in body


def test_trunk_ip_with_both_auth_sources_raises():
    """The API takes exactly one of the two; both is rejected."""
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException) as exc:
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], ip_acl_id="acl_123",
        )

    assert exc.value.param == "ip_acl_id"
    assert "not both" in str(exc.value)


def test_trunk_credential_with_ip_acl_id_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException) as exc:
        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential",
            auth_credential=CREDENTIAL, ip_acl_id="acl_123",
        )

    assert exc.value.param == "ip_acl_id"


def test_trunk_update_can_switch_to_an_ip_acl():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_1").mock(
            return_value=httpx.Response(200, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.update(
            "st_1", authentication_type="IP", ip_acl_id="acl_123"
        )

        assert json.loads(route.calls.last.request.content)["ip_acl_id"] == "acl_123"


@pytest.mark.asyncio
async def test_async_trunk_ip_with_both_auth_sources_raises():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], ip_acl_id="acl_123",
        )


def test_trunk_update_validates_auth_pairing():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.update("st_1", authentication_type="IP")


def test_trunk_update_without_auth_type_is_unaffected():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_1").mock(
            return_value=httpx.Response(200, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.update("st_1", name="Renamed")

        assert route.called


@pytest.mark.asyncio
async def test_async_trunk_create_validates_auth_pairing():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential",
        )


# --- SIP trunk transport ---
def test_trunk_udp_transport_with_ip_auth_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException) as exc:
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], transport="udp",
        )

    assert exc.value.param == "transport"
    assert "credential" in str(exc.value)


def test_trunk_udp_transport_with_credential_auth_is_allowed():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential", auth_credential=CREDENTIAL,
            transport="udp",
        )

        assert json.loads(route.calls.last.request.content)["transport"] == "udp"


def test_trunk_update_to_udp_with_ip_auth_raises():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.update(
            "st_1", authentication_type="IP", ip_acl_id="acl_123",
            transport="udp",
        )


def test_trunk_update_to_udp_without_auth_type_is_sent():
    """The trunk's current authentication_type is not known client-side."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_1").mock(
            return_value=httpx.Response(200, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.update("st_1", transport="udp")

        assert json.loads(route.calls.last.request.content)["transport"] == "udp"


@pytest.mark.asyncio
async def test_async_trunk_udp_transport_with_ip_auth_raises():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], transport="udp",
        )


@pytest.mark.parametrize("transport", ["tls", "tcp"])
def test_trunk_non_udp_transports_pass_with_ip_auth(transport):
    """Only ``udp`` is tied to an authentication_type."""
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], transport=transport,
        )

        body = json.loads(route.calls.last.request.content)
        assert body["transport"] == transport


@pytest.mark.parametrize("transport", ["tls", "tcp", "udp"])
def test_trunk_every_transport_passes_with_credential_auth(transport):
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential", auth_credential=CREDENTIAL,
            transport=transport,
        )

        body = json.loads(route.calls.last.request.content)
        assert body["transport"] == transport


@pytest.mark.parametrize("transport", ["tls", "tcp"])
def test_trunk_update_non_udp_transports_pass_with_ip_auth(transport):
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.patch(f"{BASE}/sip/trunks/st_1").mock(
            return_value=httpx.Response(200, json={"id": "st_1"})
        )
        client = Client(api_key="test_api_key")

        client.sip.trunks.update(
            "st_1", authentication_type="IP", ip_acl_id="acl_123",
            transport=transport,
        )

        body = json.loads(route.calls.last.request.content)
        assert body["transport"] == transport


def test_trunk_create_and_update_do_not_take_secure():
    """The API forbids ``secure`` and ``transport`` together, so only ``transport`` is exposed."""
    client = Client(api_key="test_api_key")

    with pytest.raises(TypeError):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential", auth_credential=CREDENTIAL,
            secure=True,
        )

    with pytest.raises(TypeError):
        client.sip.trunks.update("st_1", secure=True)


@pytest.mark.asyncio
async def test_async_trunk_udp_transport_with_credential_auth_is_allowed():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.post(f"{BASE}/sip/trunks").mock(
            return_value=httpx.Response(201, json={"id": "st_1"})
        )
        client = AsyncClient(api_key="test_api_key")

        await client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential", auth_credential=CREDENTIAL,
            transport="udp",
        )

        assert json.loads(route.calls.last.request.content)["transport"] == "udp"


# --- pagination guards reach the resource methods ---
def test_list_rejects_out_of_range_limit_before_request():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/secrets").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.secrets.list(limit=101)

        assert not route.called


def test_list_rejects_both_cursors_before_request():
    with respx.mock(assert_all_called=False) as respx_mock:
        route = respx_mock.get(f"{BASE}/events").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        client = Client(api_key="test_api_key")

        with pytest.raises(exceptions.BadParametersException):
            client.events.list(cursor_after="a", cursor_before="b")

        assert not route.called


def test_voice_app_virtual_numbers_limit_is_capped_at_fifty():
    client = Client(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        client.voice.apps.list_virtual_numbers("app_1", limit=51)


@pytest.mark.asyncio
async def test_async_list_rejects_both_cursors():
    client = AsyncClient(api_key="test_api_key")
    with pytest.raises(exceptions.BadParametersException):
        await client.sip.calls.list(cursor_after="a", cursor_before="b")
