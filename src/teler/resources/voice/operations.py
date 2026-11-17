from typing import Any, Dict, Optional, cast

from teler import constants
from teler.idempotency import resolve_idempotency_key
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    unwrap_data,
)
from .types import TransferResource

PATHS: Dict[str, str] = {
    "transfer": "/voice/calls/{}/transfer",
}


def _idempotency_headers(idempotency_key: Optional[str]) -> Dict[str, str]:
    return {"Idempotency-Key": resolve_idempotency_key(idempotency_key)}


class OperationResourceManager(BaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, TransferResource, PATHS)

    def transfer(
        self,
        call_id: str,
        target: Dict[str, Any],
        mode: str,
        timeout: Optional[int] = None,
        record: Optional[bool] = None,
        ringback: Optional[str] = None,
        dial_music: Optional[Dict[str, Any]] = None,
        confirm_sound: Optional[Dict[str, Any]] = None,
        on_failure: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
    ) -> TransferResource:
        """
        Transfer a call to a new destination.

        ``target`` is ``{"kind": ..., "number": ..., "uri": ..., "leg_id": ...,
        "custom_headers": {...}}``, where ``kind`` is ``"pstn"`` (needs
        ``number``), ``"sip"`` (needs ``uri``) or ``"leg"``. ``dial_music``,
        ``confirm_sound`` and ``on_failure`` are each ``{"action": ...,
        "media_url": ..., "text": ..., "voice": ..., "language": ...,
        "reason": ..., "loop": ...}``.
        """
        payload: Dict[str, Any] = {
            "target": target,
            "mode": mode,
            "timeout": timeout,
            "record": record,
            "ringback": ringback,
            "dial_music": dial_music,
            "confirm_sound": confirm_sound,
            "on_failure": on_failure,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

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

        res = self.client.request(
            "POST",
            self.paths["transfer"].format(call_id),
            **request_kwargs,
        )

        return cast(TransferResource, self.resource(unwrap_data(res.json())))


class AsyncOperationResourceManager(AsyncBaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, TransferResource, PATHS)

    async def transfer(
        self,
        call_id: str,
        target: Dict[str, Any],
        mode: str,
        timeout: Optional[int] = None,
        record: Optional[bool] = None,
        ringback: Optional[str] = None,
        dial_music: Optional[Dict[str, Any]] = None,
        confirm_sound: Optional[Dict[str, Any]] = None,
        on_failure: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        retry: Optional[bool] = None,
        base_retry_delay_ms: Optional[int] = None,
    ) -> TransferResource:
        """
        Asynchronously transfer a call to a new destination.

        ``target`` is ``{"kind": ..., "number": ..., "uri": ..., "leg_id": ...,
        "custom_headers": {...}}``, where ``kind`` is ``"pstn"`` (needs
        ``number``), ``"sip"`` (needs ``uri``) or ``"leg"``. ``dial_music``,
        ``confirm_sound`` and ``on_failure`` are each ``{"action": ...,
        "media_url": ..., "text": ..., "voice": ..., "language": ...,
        "reason": ..., "loop": ...}``.
        """
        payload: Dict[str, Any] = {
            "target": target,
            "mode": mode,
            "timeout": timeout,
            "record": record,
            "ringback": ringback,
            "dial_music": dial_music,
            "confirm_sound": confirm_sound,
            "on_failure": on_failure,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

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
            self.paths["transfer"].format(call_id),
            **request_kwargs,
        )

        return cast(TransferResource, self.resource(unwrap_data(res.json())))