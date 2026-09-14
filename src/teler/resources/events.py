from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResource,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
)

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
        params = build_params(
            call_id=call_id,
            type=type,
            occurred_after=occurred_after,
            delivery_status=delivery_status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), EventResource)

    def retrieve(self, id) -> EventResource:
        """
        Retrieve a single webhook event by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(id))
        return cast(EventResource, self.resource(unwrap_data(res.json())))

    def redeliver(self, id) -> EventRedeliverResult:
        """
        Redeliver a webhook event by its id.
        """
        res = self.client.request("POST", self.paths["redeliver"].format(id))
        return EventRedeliverResult(unwrap_data(res.json()))


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
        params = build_params(
            call_id=call_id,
            type=type,
            occurred_after=occurred_after,
            delivery_status=delivery_status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), EventResource)

    async def retrieve(self, id) -> EventResource:
        """
        Asynchronously retrieve a single webhook event by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(id))
        return cast(EventResource, self.resource(unwrap_data(res.json())))

    async def redeliver(self, id) -> EventRedeliverResult:
        """
        Asynchronously redeliver a webhook event by its id.
        """
        res = await self.client.request("POST", self.paths["redeliver"].format(id))
        return EventRedeliverResult(unwrap_data(res.json()))
