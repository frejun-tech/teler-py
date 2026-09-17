"""SIP trunks and calls, driven against the real API over a real socket."""
import uuid
from types import SimpleNamespace

import pytest

from teler import exceptions
from teler.resources.base import CursorPage
from teler.resources.sip.types import DeleteResult, SipCallResource, SipTrunkResource
from teler.resources.virtual_numbers import VirtualNumberResource

from .harness import ACCOUNT_ID, NOW, fake_trunk, fake_vn

TRUNKS = "app.api.routes.public.v1.sip.trunks"
CALLS = "app.api.routes.public.v1.sip.calls"
TRUNK_UUID = uuid.UUID("00000000-0000-0000-0000-0000000000d1")
CALL_ID = "cs_01JQ8Z9K7M3N2P4R5S6T7V8W9X"

CREDENTIAL = {"username": "sipuser", "password": "sippass"}
ADDRESS = {"name": "gw-1", "address": "10.0.0.1"}


def _trunk_id() -> str:
    from app.utils.identifiers import sip_trunk_id_from_uuid

    return sip_trunk_id_from_uuid(TRUNK_UUID)


@pytest.fixture
def stub_trunk_lookup(patch_crud):
    async def _ids(db, account_id, trunk_uuids):
        return [7]

    async def _attach(db, trunks):
        return None

    patch_crud(f"{TRUNKS}.get_sip_trunk_ids_from_uuids", _ids)
    patch_crud(f"{TRUNKS}.attach_sip_trunk_details", _attach)


# ------------------------------- trunks --------------------------------

def test_create_trunk_with_credential_auth(client, patch_crud, stub_trunk_lookup):
    captured = {}

    async def _create(db, account_id, trunk_data):
        captured["name"] = trunk_data.name
        captured["auth_type"] = trunk_data.authentication_type.value
        captured["username"] = trunk_data.auth_credential.username
        captured["channel_limit"] = trunk_data.channel_limit
        return fake_trunk(name=trunk_data.name)

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    trunk = client.sip.trunks.create(
        name="Main Trunk",
        domain_name="trunk.example.com",
        authentication_type="credential",
        auth_credential=CREDENTIAL,
        channel_limit=10,
        recording=True,
    )

    # The SDK payload satisfied SipTrunkCreate, which sets extra="forbid".
    assert captured["name"] == "Main Trunk"
    assert captured["auth_type"] == "credential"
    assert captured["username"] == "sipuser"
    assert captured["channel_limit"] == 10
    assert isinstance(trunk, SipTrunkResource)
    assert trunk.id.startswith("st_")
    assert trunk.cps_limit == 5


def test_create_trunk_with_ip_auth_and_inbound_route(client, patch_crud, stub_trunk_lookup):
    captured = {}

    async def _create(db, account_id, trunk_data):
        captured["addresses"] = [a.address for a in trunk_data.auth_addresses]
        captured["sip_url"] = trunk_data.inbound_route.sip_url
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    trunk = client.sip.trunks.create(
        name="IP Trunk",
        domain_name="ip.example.com",
        authentication_type="IP",
        auth_addresses=[ADDRESS],
        inbound_route={"name": "route-1", "sip_url": "sip:10.0.0.9:5060"},
    )

    assert captured["addresses"] == ["10.0.0.1"]
    assert captured["sip_url"] == "sip:10.0.0.9:5060"
    assert isinstance(trunk, SipTrunkResource)


def test_malformed_sip_url_rejected_by_real_validation(client, patch_crud, stub_trunk_lookup):
    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.sip.trunks.create(
            name="Bad Route", domain_name="x.example.com",
            authentication_type="IP", auth_addresses=[ADDRESS],
            inbound_route={"name": "r", "sip_url": "http://not-a-sip-url"},
        )


def test_short_credential_rejected_by_real_validation(client, patch_crud, stub_trunk_lookup):
    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.sip.trunks.create(
            name="T", domain_name="x.example.com",
            authentication_type="credential",
            auth_credential={"username": "ab", "password": "cd"},  # min_length is 5
        )


@pytest.mark.parametrize("transport", ["tls", "tcp", "udp"])
def test_transport_accepted_by_real_enum_with_credential_auth(
    client, patch_crud, stub_trunk_lookup, transport
):
    captured = {}

    async def _create(db, account_id, trunk_data):
        captured["transport"] = trunk_data.transport.value
        captured["fields_set"] = trunk_data.model_fields_set
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    client.sip.trunks.create(
        name="T", domain_name="t.example.com",
        authentication_type="credential", auth_credential=CREDENTIAL,
        transport=transport,
    )

    assert captured["transport"] == transport
    # 'secure' alongside 'transport' is rejected by SipTrunkCreate.
    assert "secure" not in captured["fields_set"]


@pytest.mark.parametrize("transport", ["tls", "tcp"])
def test_non_udp_transport_accepted_with_ip_auth(
    client, patch_crud, stub_trunk_lookup, transport
):
    captured = {}

    async def _create(db, account_id, trunk_data):
        captured["transport"] = trunk_data.transport.value
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    client.sip.trunks.create(
        name="T", domain_name="t.example.com", authentication_type="IP",
        auth_addresses=[ADDRESS], transport=transport,
    )

    assert captured["transport"] == transport


def test_bad_transport_value_rejected_by_real_enum(client, patch_crud, stub_trunk_lookup):
    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com",
            authentication_type="credential", auth_credential=CREDENTIAL,
            transport="sctp",
        )


def test_udp_with_ip_auth_blocked_client_side(client, patch_crud, stub_trunk_lookup):
    called = {"value": False}

    async def _create(db, account_id, trunk_data):
        called["value"] = True
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[ADDRESS], transport="udp",
        )

    assert called["value"] is False


def test_api_also_rejects_udp_with_ip_auth_when_guard_bypassed(live_api, patch_crud, stub_trunk_lookup):
    """Confirms the SDK guard mirrors real API behaviour rather than inventing it."""
    import httpx

    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.post(
            "/sip/trunks",
            json={
                "name": "T",
                "domain_name": "t.example.com",
                "authentication_type": "IP",
                "auth_addresses": [ADDRESS],
                "transport": "udp",
            },
        )

    assert res.status_code == 422
    assert "udp" in res.text.lower()


def test_api_also_rejects_udp_on_update_when_guard_bypassed(live_api, patch_crud, stub_trunk_lookup):
    import httpx

    async def _get(db, sip_trunk_id, account_id):
        return fake_trunk()

    async def _update(db, trunk_obj, data):
        return trunk_obj

    patch_crud(f"{TRUNKS}.get_sip_trunk", _get)
    patch_crud(f"{TRUNKS}.update_sip_trunk", _update)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.patch(
            f"/sip/trunks/{_trunk_id()}",
            json={"authentication_type": "IP", "ip_acl_id": None, "transport": "udp"},
        )

    assert res.status_code == 422
    assert "udp" in res.text.lower()


def test_update_to_udp_without_auth_type_reaches_the_api(client, patch_crud, stub_trunk_lookup):
    """The SDK cannot know the trunk's current authentication_type, so the API decides."""
    captured = {}

    async def _get(db, sip_trunk_id, account_id):
        return fake_trunk()

    async def _update(db, trunk_obj, data):
        captured["transport"] = data.transport.value
        return trunk_obj

    patch_crud(f"{TRUNKS}.get_sip_trunk", _get)
    patch_crud(f"{TRUNKS}.update_sip_trunk", _update)

    client.sip.trunks.update(_trunk_id(), transport="udp")

    assert captured["transport"] == "udp"


def test_cidr_auth_address_rejected_by_real_validation(client, patch_crud, stub_trunk_lookup):
    """SipAuthAddressInput parses with IPvAnyAddress, so a CIDR network is not an address."""
    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with pytest.raises(exceptions.BadParametersException):
        client.sip.trunks.create(
            name="T", domain_name="t.example.com", authentication_type="IP",
            auth_addresses=[{"name": "gw-1", "address": "203.0.113.0/24"}],
        )


def test_api_also_rejects_a_cidr_auth_address_when_guard_bypassed(live_api, patch_crud, stub_trunk_lookup):
    import httpx

    async def _create(db, account_id, trunk_data):
        return fake_trunk()

    patch_crud(f"{TRUNKS}.create_sip_trunk", _create)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.post(
            "/sip/trunks",
            json={
                "name": "T",
                "domain_name": "t.example.com",
                "authentication_type": "IP",
                "auth_addresses": [{"name": "gw-1", "address": "203.0.113.0/24"}],
            },
        )

    assert res.status_code == 422
    assert "address" in res.text.lower()


def test_api_also_requires_auth_type_on_update_when_guard_bypassed(live_api, patch_crud, stub_trunk_lookup):
    """The SDK guard mirrors SipTrunkUpdate.validate_auth_fields."""
    import httpx

    async def _get(db, sip_trunk_id, account_id):
        return fake_trunk()

    async def _update(db, trunk_obj, data):
        return trunk_obj

    patch_crud(f"{TRUNKS}.get_sip_trunk", _get)
    patch_crud(f"{TRUNKS}.update_sip_trunk", _update)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.patch(
            f"/sip/trunks/{_trunk_id()}",
            json={"auth_addresses": [{"name": "gw-1", "address": "10.0.0.1"}]},
        )

    assert res.status_code == 422
    assert "authentication type is required" in res.text.lower()


def test_api_also_rejects_an_empty_auth_address_list_when_guard_bypassed(live_api, patch_crud, stub_trunk_lookup):
    """An empty list is falsy, so it falls past the auth-material check into its own rule."""
    import httpx

    async def _get(db, sip_trunk_id, account_id):
        return fake_trunk()

    async def _update(db, trunk_obj, data):
        return trunk_obj

    patch_crud(f"{TRUNKS}.get_sip_trunk", _get)
    patch_crud(f"{TRUNKS}.update_sip_trunk", _update)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.patch(
            f"/sip/trunks/{_trunk_id()}", json={"auth_addresses": []}
        )

    assert res.status_code == 422
    assert "at least one" in res.text.lower()


def test_list_trunks_with_status_filter(client, patch_crud, stub_trunk_lookup):
    captured = {}

    async def _list(db, account_id, filters):
        captured["status"] = [s.value for s in (filters.status or [])]
        captured["limit"] = filters.limit
        return [fake_trunk()], "cur_next", None, True

    patch_crud(f"{TRUNKS}.list_sip_trunks_details_by_account", _list)

    page = client.sip.trunks.list(status=["active"], limit=20)

    assert captured == {"status": ["active"], "limit": 20}
    assert isinstance(page, CursorPage)
    assert isinstance(page.data[0], SipTrunkResource)


def test_bad_status_value_rejected_by_real_enum(client, patch_crud, stub_trunk_lookup):
    async def _list(db, account_id, filters):
        return [], None, None, False

    patch_crud(f"{TRUNKS}.list_sip_trunks_details_by_account", _list)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.sip.trunks.list(status=["bogus"])


def test_retrieve_update_delete_trunk(client, patch_crud, stub_trunk_lookup):
    async def _get(db, sip_trunk_id, account_id):
        return fake_trunk()

    async def _update(db, trunk_obj, data):
        trunk_obj.name = data.name or trunk_obj.name
        trunk_obj.is_active = data.is_active if data.is_active is not None else trunk_obj.is_active
        return trunk_obj

    async def _delete(db, trunk_obj):
        return None

    patch_crud(f"{TRUNKS}.get_sip_trunk", _get)
    patch_crud(f"{TRUNKS}.update_sip_trunk", _update)
    patch_crud(f"{TRUNKS}.delete_sip_trunk", _delete)

    got = client.sip.trunks.retrieve(_trunk_id())
    assert isinstance(got, SipTrunkResource)

    updated = client.sip.trunks.update(_trunk_id(), name="Renamed", is_active=False)
    assert updated.name == "Renamed"
    assert updated.is_active is False

    deleted = client.sip.trunks.delete(_trunk_id())
    assert isinstance(deleted, DeleteResult)
    assert deleted.success is True


def test_trunk_virtual_numbers(client, patch_crud, stub_trunk_lookup):
    async def _resolve(db, account_id, location=None, voice_app=None, sip_trunk=None):
        return {"location": None, "voice_app": None, "sip_trunk": None}

    async def _vns(db, account_id, trunk_id, filters):
        return [fake_vn()], None, None, False

    patch_crud(f"{TRUNKS}.resolve_uuid_filters", _resolve)
    patch_crud(f"{TRUNKS}.list_vns_by_sip_trunk", _vns)

    page = client.sip.trunks.list_virtual_numbers(_trunk_id())

    assert isinstance(page, CursorPage)
    assert isinstance(page.data[0], VirtualNumberResource)


# -------------------------------- calls --------------------------------

def fake_session():
    from app.db.models import CallLegRole

    leg = SimpleNamespace(
        role=CallLegRole.PRIMARY,
        duration_seconds=295,
        ended_by="callee",
        recordings=["rec_1"],
    )
    return SimpleNamespace(
        id=CALL_ID,
        account_id=ACCOUNT_ID,
        sip_trunk_id=7,
        state="completed",
        direction="inbound",
        from_number="+15550001111",
        to_number="+15550002222",
        created_at=NOW,
        answered_at=NOW,
        ended_at=NOW,
        reason="normal_clearing",
        legs=[leg],
    )


def test_list_sip_calls_with_filters(client, patch_crud):
    captured = {}

    async def _list(db, account_id, filters):
        captured["trunk_id"] = filters.trunk_id
        captured["from_number"] = filters.from_number
        captured["limit"] = filters.limit
        return [fake_session()], "cur_next", None, True

    async def _ids(db, account_id, trunk_uuids):
        return [7]

    async def _map(db, account_id, ids):
        return {7: TRUNK_UUID}

    patch_crud(f"{CALLS}.list_sip_call_sessions", _list)
    patch_crud(f"{CALLS}.get_sip_trunk_ids_from_uuids", _ids)
    patch_crud(f"{CALLS}.get_sip_trunk_uuid_map_from_ids", _map)

    page = client.sip.calls.list(
        trunk_id=_trunk_id(), from_number="+15550001111", limit=25
    )

    assert captured["trunk_id"] == 7
    assert captured["from_number"] == "+15550001111"
    assert captured["limit"] == 25
    call = page.data[0]
    assert isinstance(call, SipCallResource)
    assert call.duration_seconds == 295
    assert call.ended_by == "callee"
    assert call.recordings == ["rec_1"]
    assert call.sip_trunk_id.startswith("st_")


def test_limit_above_one_hundred_blocked_client_side(client, patch_crud):
    calls = []

    async def _list(db, account_id, filters):
        calls.append(1)
        return [], None, None, False

    patch_crud(f"{CALLS}.list_sip_call_sessions", _list)

    with pytest.raises(exceptions.BadParametersException):
        client.sip.calls.list(limit=101)

    assert calls == []


def test_retrieve_sip_call(client, patch_crud):
    async def _get(db, account_id, call_session_id, source):
        assert source == "sip_trunk"
        return fake_session()

    async def _map(db, account_id, ids):
        return {7: TRUNK_UUID}

    patch_crud(f"{CALLS}.get_call_session", _get)
    patch_crud(f"{CALLS}.get_sip_trunk_uuid_map_from_ids", _map)

    call = client.sip.calls.retrieve(CALL_ID)

    assert isinstance(call, SipCallResource)
    assert call.id == CALL_ID
    assert call.state == "completed"


def test_retrieve_malformed_call_id_is_not_found(client):
    with pytest.raises(exceptions.NotFoundException):
        client.sip.calls.retrieve("nope")


@pytest.mark.asyncio
async def test_async_retrieve_sip_call(async_client, patch_crud):
    async def _get(db, account_id, call_session_id, source):
        return fake_session()

    async def _map(db, account_id, ids):
        return {7: TRUNK_UUID}

    patch_crud(f"{CALLS}.get_call_session", _get)
    patch_crud(f"{CALLS}.get_sip_trunk_uuid_map_from_ids", _map)

    call = await async_client.sip.calls.retrieve(CALL_ID)

    assert isinstance(call, SipCallResource)
