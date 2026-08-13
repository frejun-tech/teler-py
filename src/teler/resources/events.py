from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from teler.resources.base import (AsyncBaseResourceManager, BaseResource, BaseResourceManager, CursorPage, validate_pagination)

PATHS: Dict[str, str] = {
    "list": "/events",
    "retrieve": "/events/{}",
    "redeliver": "/events/{}/redeliver",
}


@dataclass
class EventResource(BaseResource):
    """Represents a webhook event returned by the Teler API."""
    id: str
    account_id: Optional[str]
    call_id: Optional[str]
    sip_trunk_id: Optional[str]
    leg_id: Optional[str]
    type: Optional[str]
    api_version: Optional[str]
    occurred_at: Optional[str]
    payload: Optional[Dict[str, Any]]
    delivery_status: Optional[str]
    attempt_count: Optional[int]
    last_attempt_at: Optional[str]
    last_status_code: Optional[int]
    last_error: Optional[str]
    delivered_at: Optional[str]
    created_at: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class EventRedeliverResult(BaseResource):
    """Result of a webhook event redelivery request."""
    event_id: str
    redelivered_at: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


def _build_list_params(
    call_id: Optional[str],
    type: Optional[str],
    occurred_after: Optional[str],
    delivery_status: Optional[str],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    """Build the query params for listing events, dropping unset values."""
    validate_pagination(limit, cursor_after, cursor_before)
    params: Dict[str, Any] = {
        "call_id": call_id,
        "type": type,
        "occurred_after": occurred_after,
        "delivery_status": delivery_status,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


def _unwrap(body: Dict[str, Any]) -> Dict[str, Any]:
    """Unwrap a ``{"data": {...}}`` envelope if present, else return body as-is."""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _to_cursor_page(body: Dict[str, Any]) -> CursorPage:
    """Wrap a raw list response body into a typed CursorPage of EventResource."""
    return CursorPage(
        data=[EventResource(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class EventResourceManager(BaseResourceManager):
    """Synchronous manager for webhook event resources."""
    def __init__(self, client: Any):
        super().__init__(client, EventResource, PATHS)

    def list(
        self,
        call_id: Optional[str] = None,
        type: Optional[str] = None,
        occurred_after: Optional[str] = None,
        delivery_status: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List webhook events, optionally filtered, as a cursor-paginated page.
        """
        params = _build_list_params(
            call_id, type, occurred_after, delivery_status,
            limit, cursor_after, cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    def retrieve(self, id) -> EventResource:
        """
        Retrieve a single webhook event by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(id))
        return cast(EventResource, self.resource(_unwrap(res.json())))

    def redeliver(self, id) -> EventRedeliverResult:
        """
        Redeliver a webhook event by its id.
        """
        res = self.client.request("POST", self.paths["redeliver"].format(id))
        return EventRedeliverResult(_unwrap(res.json()))


class AsyncEventResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for webhook event resources."""
    def __init__(self, client: Any):
        super().__init__(client, EventResource, PATHS)

    async def list(
        self,
        call_id: Optional[str] = None,
        type: Optional[str] = None,
        occurred_after: Optional[str] = None,
        delivery_status: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list webhook events as a cursor-paginated page.
        """
        params = _build_list_params(
            call_id, type, occurred_after, delivery_status,
            limit, cursor_after, cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    async def retrieve(self, id) -> EventResource:
        """
        Asynchronously retrieve a single webhook event by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(id))
        return cast(EventResource, self.resource(_unwrap(res.json())))

    async def redeliver(self, id) -> EventRedeliverResult:
        """
        Asynchronously redeliver a webhook event by its id.
        """
        res = await self.client.request("POST", self.paths["redeliver"].format(id))
        return EventRedeliverResult(_unwrap(res.json()))
