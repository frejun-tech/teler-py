from typing import Any, Dict, Optional, cast

from teler import constants
from teler.idempotency import resolve_idempotency_key
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
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
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
    ) -> CreateCallResource:
        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record,
        )

        key = resolve_idempotency_key(idempotency_key)
        headers = {"Idempotency-Key": key}

        request_kwargs: Dict[str, Any] = {
            "json": payload,
            "headers": headers,
        }

        # Pass through retry options if provided
        if retry is not None:
            request_kwargs["retry"] = retry
        if base_retry_delay_ms is not None:
            request_kwargs["base_retry_delay_ms"] = base_retry_delay_ms
        else:
            request_kwargs["base_retry_delay_ms"] = getattr(
                constants, "CALL_CONTROL_RETRY_BASE_DELAY_MS", 300
            )
        request_kwargs["max_retry_delay_ms"] = getattr(
            constants, "MAX_RETRY_DELAY_MS", 2000
        )
        request_kwargs["timeout"] = getattr(constants, "CALL_CONTROL_TIMEOUT_MS", 5000)

        res = self.client.request(
            "POST",
            self.paths["create"],
            **request_kwargs,
        )
        return CreateCallResource(unwrap_data(res.json()))

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
        params = build_params(
            state=state,
            from_number=from_number,
            to_number=to_number,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return to_cursor_page(res.json(), CallResource)

    def retrieve(self, call_id: str) -> CallResource:
        res = self.client.request(
            "GET",
            self.paths["retrieve"].format(call_id),
        )
        return cast(
            CallResource,
            self.resource(unwrap_data(res.json())),
        )

    def list_legs(self, call_id: str) -> CursorPage:
        res = self.client.request(
            "GET",
            self.paths["legs"].format(call_id),
        )
        return to_cursor_page(res.json(), CallLegResource)


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
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
    ) -> CreateCallResource:
        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record,
        )

        key = resolve_idempotency_key(idempotency_key)
        headers = {"Idempotency-Key": key}

        request_kwargs: Dict[str, Any] = {
            "json": payload,
            "headers": headers,
        }

        if retry is not None:
            request_kwargs["retry"] = retry
        if base_retry_delay_ms is not None:
            request_kwargs["base_retry_delay_ms"] = base_retry_delay_ms
        else:
            request_kwargs["base_retry_delay_ms"] = getattr(
                constants, "CALL_CONTROL_RETRY_BASE_DELAY_MS", 300
            )
        request_kwargs["max_retry_delay_ms"] = getattr(
            constants, "MAX_RETRY_DELAY_MS", 2000
        )
        request_kwargs["timeout"] = getattr(constants, "CALL_CONTROL_TIMEOUT_MS", 5000)

        res = await self.client.request(
            "POST",
            self.paths["create"],
            **request_kwargs,
        )
        return CreateCallResource(unwrap_data(res.json()))

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
        params = build_params(
            state=state,
            from_number=from_number,
            to_number=to_number,
            created_after=created_after,
            created_before=created_before,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return to_cursor_page(res.json(), CallResource)

    async def retrieve(self, call_id: str) -> CallResource:
        res = await self.client.request(
            "GET",
            self.paths["retrieve"].format(call_id),
        )
        return cast(
            CallResource,
            self.resource(unwrap_data(res.json())),
        )

    async def list_legs(self, call_id: str) -> CursorPage:
        res = await self.client.request(
            "GET",
            self.paths["legs"].format(call_id),
        )
        return to_cursor_page(res.json(), CallLegResource)