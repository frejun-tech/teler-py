from typing import Any, Dict, Optional, cast

from teler.idempotency import resolve_idempotency_key
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    unwrap_data,
)
from .types import MutationResource

PATHS: Dict[str, str] = {
    "hangup": "/voice/calls/{}/hangup",
    "mute": "/voice/calls/{}/mute",
    "dtmf": "/voice/calls/{}/dtmf",
    "play": "/voice/calls/{}/play",
}


def _idempotency_headers(idempotency_key: Optional[str]) -> Dict[str, str]:
    return {"Idempotency-Key": resolve_idempotency_key(idempotency_key)}


class MutationResourceManager(BaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, MutationResource, PATHS)

    def hangup(
        self,
        call_id: str,
        leg_id: Optional[str] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "reason": reason,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = self.client.request(
            "POST",
            self.paths["hangup"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    def mute(
        self,
        call_id: str,
        leg_id: str,
        on: bool,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "on": on,
        }

        headers = _idempotency_headers(idempotency_key)

        res = self.client.request(
            "POST",
            self.paths["mute"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    def dtmf(
        self,
        call_id: str,
        digits: str,
        leg_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "digits": digits,
            "duration_ms": duration_ms,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = self.client.request(
            "POST",
            self.paths["dtmf"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    def play(
        self,
        call_id: str,
        media_url: str,
        leg_id: Optional[str] = None,
        loop: Optional[int] = None,
        on_dtmf: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "media_url": media_url,
            "loop": loop,
            "on_dtmf": on_dtmf,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = self.client.request(
            "POST",
            self.paths["play"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))


class AsyncMutationResourceManager(AsyncBaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, MutationResource, PATHS)

    async def hangup(
        self,
        call_id: str,
        leg_id: Optional[str] = None,
        reason: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "reason": reason,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = await self.client.request(
            "POST",
            self.paths["hangup"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    async def mute(
        self,
        call_id: str,
        leg_id: str,
        on: bool,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "on": on,
        }

        headers = _idempotency_headers(idempotency_key)

        res = await self.client.request(
            "POST",
            self.paths["mute"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    async def dtmf(
        self,
        call_id: str,
        digits: str,
        leg_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "digits": digits,
            "duration_ms": duration_ms,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = await self.client.request(
            "POST",
            self.paths["dtmf"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))

    async def play(
        self,
        call_id: str,
        media_url: str,
        leg_id: Optional[str] = None,
        loop: Optional[int] = None,
        on_dtmf: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> MutationResource:
        payload: Dict[str, Any] = {
            "leg_id": leg_id,
            "media_url": media_url,
            "loop": loop,
            "on_dtmf": on_dtmf,
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        headers = _idempotency_headers(idempotency_key)

        res = await self.client.request(
            "POST",
            self.paths["play"].format(call_id),
            json=payload,
            headers=headers,
        )

        return cast(MutationResource, self.resource(unwrap_data(res.json())))