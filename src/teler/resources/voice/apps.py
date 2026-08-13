from typing import Any, Dict, Optional, List, cast

from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    validate_pagination,
)
from .types import VoiceAppResource, VirtualNumberResource, DeleteResult


PATHS: Dict[str, str] = {
    "create": "/voice/apps",
    "list": "/voice/apps",
    "retrieve": "/voice/apps/{}",
    "update": "/voice/apps/{}",
    "delete": "/voice/apps/{}",
    "virtual_numbers": "/voice/apps/{}/virtual-numbers",
}


def _build_list_params(
    search: Optional[str],
    status: Optional[List[str]],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    validate_pagination(limit, cursor_after, cursor_before)
    params: Dict[str, Any] = {
        "search": search,
        "status": status,
        "limit": limit,
        "cursor_after": cursor_after,
        "cursor_before": cursor_before,
    }
    return {k: v for k, v in params.items() if v is not None}


def _build_vn_params(
    search: Optional[str],
    location: Optional[List[str]],
    limit: int,
    cursor_after: Optional[str],
    cursor_before: Optional[str],
) -> Dict[str, Any]:
    # This endpoint narrows the page size to 50, unlike the usual 100.
    validate_pagination(limit, cursor_after, cursor_before, max_limit=50)
    params: Dict[str, Any] = {
        "search": search,
        "location": location,
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


class AppResourceManager(BaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, VoiceAppResource, PATHS)

    def create(
        self,
        name: str,
        flow_url: str,
        webhook_url: str,
        fallback_url: Optional[str] = None,
        vn_ids: Optional[List[str]] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        channel_limit: Optional[int] = None,
    ) -> VoiceAppResource:
        payload: Dict[str, Any] = {
            "name": name,
            "flow_url": flow_url,
            "webhook_url": webhook_url,
            "fallback_url": fallback_url,
            "vn_ids": vn_ids,
            "secret_id": secret_id,
            "webhook_api_version": webhook_api_version,
            "channel_limit": channel_limit,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        res = self.client.request("POST", self.paths["create"], json=payload)
        return cast(VoiceAppResource, self.resource(_unwrap(res.json())))

    def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_list_params(
            search,
            status,
            limit,
            cursor_after,
            cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return _to_cursor_page(res.json(), VoiceAppResource)

    def retrieve(self, voice_app_id: str) -> VoiceAppResource:
        res = self.client.request(
            "GET",
            self.paths["retrieve"].format(voice_app_id),
        )
        return cast(
            VoiceAppResource,
            self.resource(_unwrap(res.json())),
        )

    def update(
        self,
        voice_app_id: str,
        name: Optional[str] = None,
        flow_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        fallback_url: Optional[str] = None,
        status: Optional[str] = None,
        channel_limit: Optional[int] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
    ) -> VoiceAppResource:
        payload: Dict[str, Any] = {
            "name": name,
            "flow_url": flow_url,
            "webhook_url": webhook_url,
            "fallback_url": fallback_url,
            "status": status,
            "channel_limit": channel_limit,
            "secret_id": secret_id,
            "webhook_api_version": webhook_api_version,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        res = self.client.request(
            "PATCH",
            self.paths["update"].format(voice_app_id),
            json=payload,
        )
        return cast(
            VoiceAppResource,
            self.resource(_unwrap(res.json())),
        )

    def delete(self, voice_app_id: str) -> DeleteResult:
        res = self.client.request(
            "DELETE",
            self.paths["delete"].format(voice_app_id),
        )
        return DeleteResult(_unwrap(res.json()))

    def list_virtual_numbers(
        self,
        voice_app_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_vn_params(
            search,
            location,
            limit,
            cursor_after,
            cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(voice_app_id),
            params=params,
        )
        return _to_cursor_page(res.json(), VirtualNumberResource)


class AsyncAppResourceManager(AsyncBaseResourceManager):
    def __init__(self, client: Any):
        super().__init__(client, VoiceAppResource, PATHS)

    async def create(
        self,
        name: str,
        flow_url: str,
        webhook_url: str,
        fallback_url: Optional[str] = None,
        vn_ids: Optional[List[str]] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
        channel_limit: Optional[int] = None,
    ) -> VoiceAppResource:
        payload: Dict[str, Any] = {
            "name": name,
            "flow_url": flow_url,
            "webhook_url": webhook_url,
            "fallback_url": fallback_url,
            "vn_ids": vn_ids,
            "secret_id": secret_id,
            "webhook_api_version": webhook_api_version,
            "channel_limit": channel_limit,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        res = await self.client.request(
            "POST",
            self.paths["create"],
            json=payload,
        )
        return cast(
            VoiceAppResource,
            self.resource(_unwrap(res.json())),
        )

    async def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_list_params(
            search,
            status,
            limit,
            cursor_after,
            cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return _to_cursor_page(res.json(), VoiceAppResource)

    async def retrieve(self, voice_app_id: str) -> VoiceAppResource:
        res = await self.client.request(
            "GET",
            self.paths["retrieve"].format(voice_app_id),
        )
        return cast(
            VoiceAppResource,
            self.resource(_unwrap(res.json())),
        )

    async def update(
        self,
        voice_app_id: str,
        name: Optional[str] = None,
        flow_url: Optional[str] = None,
        webhook_url: Optional[str] = None,
        fallback_url: Optional[str] = None,
        status: Optional[str] = None,
        channel_limit: Optional[int] = None,
        secret_id: Optional[str] = None,
        webhook_api_version: Optional[str] = None,
    ) -> VoiceAppResource:
        payload: Dict[str, Any] = {
            "name": name,
            "flow_url": flow_url,
            "webhook_url": webhook_url,
            "fallback_url": fallback_url,
            "status": status,
            "channel_limit": channel_limit,
            "secret_id": secret_id,
            "webhook_api_version": webhook_api_version,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        res = await self.client.request(
            "PATCH",
            self.paths["update"].format(voice_app_id),
            json=payload,
        )
        return cast(
            VoiceAppResource,
            self.resource(_unwrap(res.json())),
        )

    async def delete(self, voice_app_id: str) -> DeleteResult:
        res = await self.client.request(
            "DELETE",
            self.paths["delete"].format(voice_app_id),
        )
        return DeleteResult(_unwrap(res.json()))

    async def list_virtual_numbers(
        self,
        voice_app_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        params = _build_vn_params(
            search,
            location,
            limit,
            cursor_after,
            cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(voice_app_id),
            params=params,
        )
        return _to_cursor_page(res.json(), VirtualNumberResource)