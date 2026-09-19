"""Events, driven against the real API over a real socket.

Two things here can only be proven with the real API in the loop:

* ``WebhookEventResponse.event_type`` carries ``alias="type"``. The SDK reads
  ``type``, so if FastAPI serialized it under the field name instead,
  ``EventResource.type`` would read back ``None``. Only a real response settles
  which key lands on the wire.
* redelivery outside the replay window really returns 410, which is the status
  the SDK had unmapped until now.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from teler import exceptions
from teler.resources.base import CursorPage
from teler.resources.events import EventRedeliverResult, EventResource

from .harness import ACCOUNT_ID, NOW

CRUD = "app.crud.events"
ROUTE = "app.api.routes.public.v1.events"

# Event ids are `evt_` plus a 26-character ULID; the route rejects anything else
# via is_valid_id before touching the database.
EVENT_ID = "evt_01JQ8Z9K7M3N2P4R5S6T7V8W9X"


def _event_id() -> str:
    return EVENT_ID


def fake_event():
    return SimpleNamespace(
        id=_event_id(),
        account_id=ACCOUNT_ID,
        call_id=None,
        sip_trunk_id=None,
        leg_id=None,
        event_type="call.completed",
        api_version="2026-06-01",
        occurred_at=NOW,
        payload={"type": "call.completed"},
        delivery_status="delivered",
        attempt_count=1,
        last_attempt_at=NOW,
        last_status_code=200,
        last_error=None,
        delivered_at=NOW,
        created_at=NOW,
    )


def test_list_events_parses_the_aliased_type_field(client, patch_crud):
    async def _list(db, account_id, filters):
        return [fake_event()], "cur_next", None, True

    patch_crud(f"{CRUD}.list_webhook_events", _list)

    page = client.events.list()

    assert isinstance(page, CursorPage)
    event = page.data[0]
    assert isinstance(event, EventResource)
    # Proves the wire key is "type", not "event_type".
    assert event.type == "call.completed"
    assert event.account_id.startswith("acc_")
    assert event.attempt_count == 1


def test_list_events_filters_survive_real_validation(client, patch_crud):
    captured = {}

    async def _list(db, account_id, filters):
        captured["delivery_status"] = filters.delivery_status
        captured["event_type"] = filters.event_type
        captured["limit"] = filters.limit
        captured["occurred_after"] = filters.occurred_after
        return [], None, None, False

    patch_crud(f"{CRUD}.list_webhook_events", _list)

    client.events.list(
        delivery_status="delivered",
        type="call.completed",
        occurred_after="2026-08-01T00:00:00Z",
        limit=10,
    )

    assert captured["delivery_status"].value == "delivered"
    assert captured["event_type"] == "call.completed"
    assert captured["limit"] == 10
    assert isinstance(captured["occurred_after"], datetime)


def test_bad_delivery_status_is_rejected_by_the_real_enum(client, patch_crud):
    async def _list(db, account_id, filters):
        return [], None, None, False

    patch_crud(f"{CRUD}.list_webhook_events", _list)

    with pytest.raises(exceptions.UnprocessableRequestException):
        client.events.list(delivery_status="not_a_status")


def test_retrieve_event(client, patch_crud):
    async def _get(db, account_id, event_id):
        return fake_event()

    patch_crud(f"{CRUD}.get_webhook_event", _get)

    event = client.events.retrieve(_event_id())

    assert isinstance(event, EventResource)
    assert event.type == "call.completed"
    assert event.payload == {"type": "call.completed"}


def test_retrieve_malformed_event_id_is_not_found(client):
    with pytest.raises(exceptions.NotFoundException):
        client.events.retrieve("nope")


def test_redeliver_returns_202_and_parses(client, patch_crud):
    async def _get(db, account_id, event_id):
        return fake_event()

    async def _redeliver(db, event):
        return datetime(2026, 8, 17, 13, 0, 0, tzinfo=timezone.utc)

    patch_crud(f"{CRUD}.get_webhook_event", _get)
    patch_crud(f"{ROUTE}.redeliver_event", _redeliver)

    result = client.events.redeliver(_event_id())

    assert isinstance(result, EventRedeliverResult)
    assert result.event_id == _event_id()
    assert result.redelivered_at.startswith("2026-08-17T13:00:00")


def test_redeliver_outside_window_raises_gone(client, patch_crud):
    """The 410 mapping added to STATUS_EXCEPTIONS, proven against the real API."""
    from app.services.webhooks.replayer import REPLAY_TOO_OLD, ReplayError

    async def _get(db, account_id, event_id):
        return fake_event()

    async def _redeliver(db, event):
        raise ReplayError(REPLAY_TOO_OLD, http_status=410)

    patch_crud(f"{CRUD}.get_webhook_event", _get)
    patch_crud(f"{ROUTE}.redeliver_event", _redeliver)

    with pytest.raises(exceptions.GoneException) as excinfo:
        client.events.redeliver(_event_id())

    assert excinfo.value.code == 410


def test_redeliver_not_redeliverable_raises_conflict(client, patch_crud):
    from app.services.webhooks.replayer import (REPLAY_NOT_REDELIVERABLE,
                                                 ReplayError)

    async def _get(db, account_id, event_id):
        return fake_event()

    async def _redeliver(db, event):
        raise ReplayError(REPLAY_NOT_REDELIVERABLE, http_status=409)

    patch_crud(f"{CRUD}.get_webhook_event", _get)
    patch_crud(f"{ROUTE}.redeliver_event", _redeliver)

    with pytest.raises(exceptions.ConflictException):
        client.events.redeliver(_event_id())


def test_both_cursors_are_rejected_client_side(client, patch_crud):
    """The SDK guard fires before the request; the API would also 422."""
    calls = []

    async def _list(db, account_id, filters):
        calls.append(1)
        return [], None, None, False

    patch_crud(f"{CRUD}.list_webhook_events", _list)

    with pytest.raises(exceptions.BadParametersException):
        client.events.list(cursor_after="a", cursor_before="b")

    assert calls == []


@pytest.mark.asyncio
async def test_async_retrieve_event(async_client, patch_crud):
    async def _get(db, account_id, event_id):
        return fake_event()

    patch_crud(f"{CRUD}.get_webhook_event", _get)

    event = await async_client.events.retrieve(_event_id())

    assert isinstance(event, EventResource)
    assert event.type == "call.completed"
