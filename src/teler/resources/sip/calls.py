from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
)
from .types import SipCallResource

PATHS: Dict[str, str] = {
    "list": "/sip/calls",
    "retrieve": "/sip/calls/{}",
}


def _build_list_params(
    trunk_id: Optional[str],
    from_number: Optional[str],
    to_number: Optional[str],
    created_after: Optional[str],
    created_before: Optional[str],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    """Build the query params for listing SIP calls, dropping unset values."""
    params: Dict[str, Any] = {
        "trunk_id": trunk_id,
        "from_number": from_number,
        "to_number": to_number,
        "created_after": created_after,
        "created_before": created_before,
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
    """Wrap a raw list response body into a typed CursorPage of SipCallResource."""
    return CursorPage(
        data=[SipCallResource(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class SipCallResourceManager(BaseResourceManager):
    """Synchronous manager for SIP call resources."""
    def __init__(self, client: Any):
        super().__init__(client, SipCallResource, PATHS)

    def list(
        self,
        trunk_id: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List SIP calls, optionally filtered, as a cursor-paginated page.
        """
        params = _build_list_params(
            trunk_id, from_number, to_number,
            created_after, created_before,
            limit, cursor_after, cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    def retrieve(self, call_id: str) -> SipCallResource:
        """
        Retrieve a single SIP call by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(call_id))
        return cast(SipCallResource, self.resource(_unwrap(res.json())))


class AsyncSipCallResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for SIP call resources."""
    def __init__(self, client: Any):
        super().__init__(client, SipCallResource, PATHS)

    async def list(
        self,
        trunk_id: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list SIP calls as a cursor-paginated page.
        """
        params = _build_list_params(
            trunk_id, from_number, to_number,
            created_after, created_before,
            limit, cursor_after, cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return _to_cursor_page(res.json())

    async def retrieve(self, call_id: str) -> SipCallResource:
        """
        Asynchronously retrieve a single SIP call by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(call_id))
        return cast(SipCallResource, self.resource(_unwrap(res.json())))
