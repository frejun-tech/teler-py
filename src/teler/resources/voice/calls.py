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
        from_number: str = None,
        to_number: str = None,
        flow_url: str = None,
        status_callback_url: str = None,
        record: bool = True,
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> CreateCallResource:
        # Allow alternative calling conventions
        if "fromNumber" in kwargs:
            from_number = kwargs.pop("fromNumber")
        if "toNumber" in kwargs:
            to_number = kwargs.pop("toNumber")
        if "flowUrl" in kwargs:
            flow_url = kwargs.pop("flowUrl")
        if "statusCallbackUrl" in kwargs:
            status_callback_url = kwargs.pop("statusCallbackUrl")
        if "idempotencyKey" in kwargs and idempotency_key is None:
            idempotency_key = kwargs.pop("idempotencyKey")
        if "baseRetryDelayMs" in kwargs and base_retry_delay_ms is None:
            base_retry_delay_ms = kwargs.pop("baseRetryDelayMs")
        if "idempotency_key" in kwargs and idempotency_key is None:
            idempotency_key = kwargs.pop("idempotency_key")

        # Handle positional args for flexibility (e.g., if called with different patterns)
        # Check if first arg after self is a dict
        if isinstance(from_number, dict):
            payload_dict = from_number
            from_number = payload_dict.get("from_number") or payload_dict.get("fromNumber")
            to_number = payload_dict.get("to_number") or payload_dict.get("toNumber")
            flow_url = payload_dict.get("flow_url") or payload_dict.get("flowUrl")
            status_callback_url = payload_dict.get("status_callback_url") or payload_dict.get("statusCallbackUrl")
            if record is True and "record" in payload_dict:
                record = payload_dict.get("record")
            # shift args
            if len(args) > 0 and idempotency_key is None:
                idempotency_key = args[0]
            if len(args) > 1 and retry is None:
                retry = args[1]
            if len(args) > 2 and base_retry_delay_ms is None:
                base_retry_delay_ms = args[2]
        else:
            # Shift positional args if they were passed in non-standard positions
            # e.g., (from, to, flow, status, record, idempotency_key, ...)
            idx = 0
            # args start from 6th positional effectively
            if len(args) > idx and idempotency_key is None and isinstance(args[idx], str):
                idempotency_key = args[idx]
                idx += 1
            elif len(args) > idx and idempotency_key is None:
                # might be bool
                pass
            if len(args) > idx and retry is None and isinstance(args[idx], bool):
                retry = args[idx]
                idx += 1
            if len(args) > idx and base_retry_delay_ms is None and isinstance(args[idx], int):
                base_retry_delay_ms = args[idx]
                idx += 1

        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record if record is not None else True,
        )
        if payload.get("record") is None:
            payload["record"] = True

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
        from_number: str = None,
        to_number: str = None,
        flow_url: str = None,
        status_callback_url: str = None,
        record: bool = True,
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
        *args: Any,
        **kwargs: Any,
    ) -> CreateCallResource:
        if "fromNumber" in kwargs:
            from_number = kwargs.pop("fromNumber")
        if "toNumber" in kwargs:
            to_number = kwargs.pop("toNumber")
        if "flowUrl" in kwargs:
            flow_url = kwargs.pop("flowUrl")
        if "statusCallbackUrl" in kwargs:
            status_callback_url = kwargs.pop("statusCallbackUrl")
        if "idempotencyKey" in kwargs and idempotency_key is None:
            idempotency_key = kwargs.pop("idempotencyKey")
        if "baseRetryDelayMs" in kwargs and base_retry_delay_ms is None:
            base_retry_delay_ms = kwargs.pop("baseRetryDelayMs")
        if "idempotency_key" in kwargs and idempotency_key is None:
            idempotency_key = kwargs.pop("idempotency_key")

        if isinstance(from_number, dict):
            payload_dict = from_number
            from_number = payload_dict.get("from_number") or payload_dict.get("fromNumber")
            to_number = payload_dict.get("to_number") or payload_dict.get("toNumber")
            flow_url = payload_dict.get("flow_url") or payload_dict.get("flowUrl")
            status_callback_url = payload_dict.get("status_callback_url") or payload_dict.get("statusCallbackUrl")
            if record is True and "record" in payload_dict:
                record = payload_dict.get("record")
            if len(args) > 0 and idempotency_key is None:
                idempotency_key = args[0]
            if len(args) > 1 and retry is None:
                retry = args[1]
            if len(args) > 2 and base_retry_delay_ms is None:
                base_retry_delay_ms = args[2]
        else:
            idx = 0
            if len(args) > idx and idempotency_key is None and isinstance(args[idx], str) and not isinstance(args[idx], bool):
                # Could be idempotency key
                idempotency_key = args[idx]
                idx += 1
            elif len(args) > idx and retry is None and isinstance(args[idx], bool):
                retry = args[idx]
                idx += 1
            if len(args) > idx and base_retry_delay_ms is None and isinstance(args[idx], int) and not isinstance(args[idx], bool):
                base_retry_delay_ms = args[idx]
                idx += 1

        payload = _build_create_payload(
            from_number,
            to_number,
            flow_url,
            status_callback_url,
            record if record is not None else True,
        )
        if payload.get("record") is None:
            payload["record"] = True

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