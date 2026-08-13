from typing import Any, Dict, Optional, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
)
from .types import CallResource, CallLegResource, CreateCallResource

PATHS: Dict[str, str] = {
    "create": "/voice/calls/initiate",
    "list": "/voice/calls",
    "retrieve": "/voice/calls/{}",
    "legs": "/voice/calls/{}/legs",
}


def _build_create_payload(
    from_number: str,
    to_number: str,
    flow_url: str,
    status_callback_url: str,
    record: bool,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "from_number": from_number,
        "to_number": to_number,
        "flow_url": flow_url,
        "status_callback_url": status_callback_url,
        "record": record,
    }
    return {k: v for k, v in payload.items() if v is not None}


def _build_list_params(
    state: Optional[str],
    from_number: Optional[str],
    to_number: Optional[str],
    created_after: Optional[str],
    created_before: Optional[str],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "state": state,
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
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        return body["data"]
    return body


def _to_cursor_page(body: Dict[str, Any], resource_cls) -> CursorPage:
    return CursorPage(
        data=[resource_cls(item) for item in body.get("data", [])],
        next_cursor=body.get("next_cursor"),
        previous_cursor=body.get("previous_cursor"),
        has_more=body.get("has_more", False),
    )


class CallResourceManager(BaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, CallResource, PATHS)

    def create(
        self,
        from_number: str,
        to_number: str,
        flow_url: str,
        status_callback_url: str,
        record: bool = True,
    ) -> CreateCallResource:
        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record,
        )
        res = self.client.request(
            "POST",
            self.paths["create"],
            json=payload,
        )
        return CreateCallResource(_unwrap(res.json()))

    def list(
        self,
        state: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_list_params(
            state,
            from_number,
            to_number,
            created_after,
            created_before,
            limit,
            cursor_after,
            cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return _to_cursor_page(res.json(), CallResource)

    def retrieve(self, call_id: str) -> CallResource:
        res = self.client.request(
            "GET",
            self.paths["retrieve"].format(call_id),
        )
        return cast(
            CallResource,
            self.resource(_unwrap(res.json())),
        )

    def get_legs(self, call_id: str) -> CursorPage:
        res = self.client.request(
            "GET",
            self.paths["legs"].format(call_id),
        )
        return _to_cursor_page(res.json(), CallLegResource)


class AsyncCallResourceManager(AsyncBaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, CallResource, PATHS)

    async def create(
        self,
        from_number: str,
        to_number: str,
        flow_url: str,
        status_callback_url: str,
        record: bool = True,
    ) -> CreateCallResource:
        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record,
        )
        res = await self.client.request(
            "POST",
            self.paths["create"],
            json=payload,
        )
        return CreateCallResource(_unwrap(res.json()))

    async def list(
        self,
        state: Optional[str] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_list_params(
            state,
            from_number,
            to_number,
            created_after,
            created_before,
            limit,
            cursor_after,
            cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return _to_cursor_page(res.json(), CallResource)

    async def retrieve(self, call_id: str) -> CallResource:
        res = await self.client.request(
            "GET",
            self.paths["retrieve"].format(call_id),
        )
        return cast(
            CallResource,
            self.resource(_unwrap(res.json())),
        )

    async def get_legs(self, call_id: str) -> CursorPage:
        res = await self.client.request(
            "GET",
            self.paths["legs"].format(call_id),
        )
        return _to_cursor_page(res.json(), CallLegResource)