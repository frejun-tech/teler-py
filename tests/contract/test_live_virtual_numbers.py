"""Virtual numbers, driven against the real API over a real socket."""
import uuid

import pytest

from teler import exceptions
from teler.resources.base import CursorPage
from teler.resources.virtual_numbers import VirtualNumberResource, VNActionResult

from .harness import fake_vn

ROUTE = "app.api.routes.public.v1.vns"
VN_UUID = uuid.UUID("00000000-0000-0000-0000-0000000000c1")
APP_UUID = uuid.UUID("00000000-0000-0000-0000-0000000000d9")
TRUNK_UUID = uuid.UUID("00000000-0000-0000-0000-0000000000d1")


def _vn_id() -> str:
    from app.utils.identifiers import vn_id_from_uuid

    return vn_id_from_uuid(VN_UUID)


def _app_id() -> str:
    from app.utils.identifiers import call_app_id_from_uuid

    return call_app_id_from_uuid(APP_UUID)


def _trunk_id() -> str:
    from app.utils.identifiers import sip_trunk_id_from_uuid

    return sip_trunk_id_from_uuid(TRUNK_UUID)


@pytest.fixture
def stub_filters(patch_crud):
    """Stand in for resolve_uuid_filters, recording the raw query values.

    The real resolver turns prefixed ids into UUIDs, which the filters model
    requires (BaseVNFilters.location is list[UUID]), so the stub must too.
    """
    seen = {}

    async def _resolve(db, account_id, location=None, voice_app=None, sip_trunk=None):
        from app.utils.identifiers import uuid_from_loc_id

        seen["location"] = location
        seen["voice_app"] = voice_app
        seen["sip_trunk"] = sip_trunk
        return {
            "location": [uuid_from_loc_id(x) for x in location] if location else None,
            "voice_app": None,
            "sip_trunk": None,
        }

    patch_crud(f"{ROUTE}.resolve_uuid_filters", _resolve)
    return seen


def _loc_id(suffix: int) -> str:
    from app.utils.identifiers import loc_id_from_uuid

    return loc_id_from_uuid(uuid.UUID(f"00000000-0000-0000-0000-0000000000{suffix:02x}"))


def test_list_sends_repeated_filter_params(client, patch_crud, stub_filters):
    captured = {}

    async def _list(db, account_id, filters):
        captured["limit"] = filters.limit
        captured["search"] = filters.search
        captured["location"] = filters.location
        return [fake_vn()], "cur_next", None, True

    patch_crud(f"{ROUTE}.list_vns_by_account", _list)

    locations = [_loc_id(0xb1), _loc_id(0xb2)]
    page = client.virtual_numbers.list(
        search="Support", location=locations, limit=25
    )

    # A list filter must arrive as repeated query params, not a joined string.
    assert stub_filters["location"] == locations
    assert captured["search"] == "Support"
    assert captured["limit"] == 25
    assert isinstance(page, CursorPage)
    vn = page.data[0]
    assert isinstance(vn, VirtualNumberResource)
    assert vn.id.startswith("vn_")
    assert vn.account_id.startswith("acc_")
    assert vn.location["region_code"] == "NY"


def test_assign_to_voice_app(client, patch_crud, stub_filters):
    captured = {}

    async def _resolve_ids(db, account, apply_to_all, vn_ids_input, **kw):
        captured["vn_ids"] = vn_ids_input
        captured["apply_to_all"] = apply_to_all
        return [VN_UUID]

    async def _verify_app(db, account_id, call_app_id):
        captured["call_app_id"] = call_app_id
        return True

    async def _assign(db, vn_ids, call_app_id):
        return len(vn_ids)

    patch_crud(f"{ROUTE}.resolve_and_verify_vn_ids", _resolve_ids)
    patch_crud(f"{ROUTE}.verify_call_app_ownership", _verify_app)
    patch_crud(f"{ROUTE}.assign_vns_to_call_app", _assign)

    result = client.virtual_numbers.assign(
        vn_ids=[_vn_id()], voice_app_id=_app_id()
    )

    assert captured["vn_ids"] == [_vn_id()]
    assert captured["apply_to_all"] is False
    assert captured["call_app_id"] == APP_UUID
    assert isinstance(result, VNActionResult)
    assert result.success is True
    assert "1 virtual numbers" in result.message


def test_assign_to_sip_trunk(client, patch_crud, stub_filters):
    async def _resolve_ids(db, account, apply_to_all, vn_ids_input, **kw):
        return [VN_UUID]

    async def _trunk_ids(db, account_id, trunk_uuids):
        return [7]

    async def _verify_trunk(db, account_id, sip_trunk_id):
        return True

    async def _assign(db, vn_ids, sip_trunk_id):
        return len(vn_ids)

    patch_crud(f"{ROUTE}.resolve_and_verify_vn_ids", _resolve_ids)
    patch_crud(f"{ROUTE}.get_sip_trunk_ids_from_uuids", _trunk_ids)
    patch_crud(f"{ROUTE}.verify_sip_trunk_ownership", _verify_trunk)
    patch_crud(f"{ROUTE}.assign_vns_to_sip_trunk", _assign)

    result = client.virtual_numbers.assign(
        apply_to_all=True, sip_trunk_id=_trunk_id()
    )

    assert isinstance(result, VNActionResult)
    assert result.success is True


def test_assign_with_both_targets_blocked_client_side(client, patch_crud):
    """The SDK guard fires first; the API would answer 400."""
    calls = []

    async def _resolve_ids(db, account, apply_to_all, vn_ids_input, **kw):
        calls.append(1)
        return [VN_UUID]

    patch_crud(f"{ROUTE}.resolve_and_verify_vn_ids", _resolve_ids)

    with pytest.raises(exceptions.BadParametersException):
        client.virtual_numbers.assign(
            vn_ids=[_vn_id()], voice_app_id=_app_id(), sip_trunk_id=_trunk_id()
        )

    assert calls == []


def test_api_also_rejects_both_targets_when_guard_bypassed(live_api, patch_crud):
    """Confirms the SDK guard mirrors real API behaviour rather than inventing it."""
    import httpx

    async def _resolve_ids(db, account, apply_to_all, vn_ids_input, **kw):
        return [VN_UUID]

    patch_crud(f"{ROUTE}.resolve_and_verify_vn_ids", _resolve_ids)

    with httpx.Client(
        base_url=live_api.base_url, headers={"x-api-key": "test_api_key"}
    ) as raw:
        res = raw.post(
            "/virtual-numbers/assign",
            json={
                "vn_ids": [_vn_id()],
                "voice_app_id": _app_id(),
                "sip_trunk_id": _trunk_id(),
            },
        )

    assert res.status_code == 400
    assert "both" in res.text.lower()


def test_unassign(client, patch_crud, stub_filters):
    async def _resolve_ids(db, account, apply_to_all, vn_ids_input, **kw):
        return [VN_UUID]

    async def _unassign(db, vn_ids):
        return len(vn_ids)

    patch_crud(f"{ROUTE}.resolve_and_verify_vn_ids", _resolve_ids)
    patch_crud(f"{ROUTE}.unassign_vns", _unassign)

    result = client.virtual_numbers.unassign(vn_ids=[_vn_id()])

    assert isinstance(result, VNActionResult)
    assert result.success is True


def test_update_name(client, patch_crud):
    captured = {}

    async def _get_vn(db, vn_uuid, account_id):
        return fake_vn()

    async def _update(db, vn_obj, data, account_id):
        captured["name"] = data.name
        vn_obj.name = data.name
        return vn_obj

    patch_crud(f"{ROUTE}.get_vn", _get_vn)
    patch_crud(f"{ROUTE}.update_vn", _update)

    vn = client.virtual_numbers.update(_vn_id(), name="Renamed Line")

    assert captured["name"] == "Renamed Line"
    assert isinstance(vn, VirtualNumberResource)
    assert vn.name == "Renamed Line"


def test_update_with_blank_name_rejected_by_real_validation(client, patch_crud):
    async def _get_vn(db, vn_uuid, account_id):
        return fake_vn()

    patch_crud(f"{ROUTE}.get_vn", _get_vn)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.virtual_numbers.update(_vn_id(), name="   ")


@pytest.mark.asyncio
async def test_async_list(async_client, patch_crud, stub_filters):
    async def _list(db, account_id, filters):
        return [fake_vn()], None, None, False

    patch_crud(f"{ROUTE}.list_vns_by_account", _list)

    page = await async_client.virtual_numbers.list()

    assert isinstance(page, CursorPage)
    assert isinstance(page.data[0], VirtualNumberResource)
