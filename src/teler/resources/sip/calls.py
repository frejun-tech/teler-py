from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
)
from .types import SipCallResource

PATHS: Dict[str, str] = {
    "list": "/sip/calls",
    "retrieve": "/sip/calls/{}",
}


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
        params = build_params(
            trunk_id=trunk_id,
            from_number=from_number,
            to_number=to_number,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SipCallResource)

    def retrieve(self, call_id: str) -> SipCallResource:
        """
        Retrieve a single SIP call by its id.
        """
        res = self.client.request("GET", self.paths["retrieve"].format(call_id))
        return cast(SipCallResource, self.resource(unwrap_data(res.json())))


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
        params = build_params(
            trunk_id=trunk_id,
            from_number=from_number,
            to_number=to_number,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request("GET", self.paths["list"], params=params)
        return to_cursor_page(res.json(), SipCallResource)

    async def retrieve(self, call_id: str) -> SipCallResource:
        """
        Asynchronously retrieve a single SIP call by its id.
        """
        res = await self.client.request("GET", self.paths["retrieve"].format(call_id))
        return cast(SipCallResource, self.resource(unwrap_data(res.json())))
