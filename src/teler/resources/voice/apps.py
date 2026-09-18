from typing import Any, Dict, Optional, List, cast

from teler import constants
from teler.resources.base import (
    AsyncBaseResourceManager,
    BaseResourceManager,
    CursorPage,
    build_params,
    to_cursor_page,
    unwrap_data,
    validate_webhook_api_version,
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


class AppResourceManager(BaseResourceManager):
    """Synchronous manager for voice app resources."""
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
        webhook_api_version: str = constants.WEBHOOK_API_VERSION,
        channel_limit: Optional[int] = None,
    ) -> VoiceAppResource:
        """
        Create a voice app.

        ``vn_ids`` is a list of virtual number ids to assign to the app.
        """
        validate_webhook_api_version(webhook_api_version)
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
        return cast(VoiceAppResource, self.resource(unwrap_data(res.json())))

    def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List voice apps, optionally filtered, as a cursor-paginated page.
        """
        params = build_params(
            search=search,
            status=status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return to_cursor_page(res.json(), VoiceAppResource)

    def retrieve(self, voice_app_id: str) -> VoiceAppResource:
        """
        Retrieve a single voice app by its id.
        """
        res = self.client.request(
            "GET",
            self.paths["retrieve"].format(voice_app_id),
        )
        return cast(
            VoiceAppResource,
            self.resource(unwrap_data(res.json())),
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
        """
        Update a voice app by its id.
        """
        validate_webhook_api_version(webhook_api_version)
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
            self.resource(unwrap_data(res.json())),
        )

    def delete(self, voice_app_id: str) -> DeleteResult:
        """
        Delete a voice app by its id.
        """
        res = self.client.request(
            "DELETE",
            self.paths["delete"].format(voice_app_id),
        )
        return DeleteResult(unwrap_data(res.json()))

    def list_virtual_numbers(
        self,
        voice_app_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        List the virtual numbers assigned to a voice app.
        """
        params = build_params(
            search=search,
            location=location,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
            max_limit=50,
        )
        res = self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(voice_app_id),
            params=params,
        )
        return to_cursor_page(res.json(), VirtualNumberResource)


class AsyncAppResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for voice app resources."""
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
        webhook_api_version: str = constants.WEBHOOK_API_VERSION,
        channel_limit: Optional[int] = None,
    ) -> VoiceAppResource:
        """
        Asynchronously create a voice app.
        """
        validate_webhook_api_version(webhook_api_version)
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
            self.resource(unwrap_data(res.json())),
        )

    async def list(
        self,
        search: Optional[str] = None,
        status: Optional[List[str]] = None,
        limit: int = 50,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list voice apps as a cursor-paginated page.
        """
        params = build_params(
            search=search,
            status=status,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
        )
        res = await self.client.request(
            "GET",
            self.paths["list"],
            params=params,
        )
        return to_cursor_page(res.json(), VoiceAppResource)

    async def retrieve(self, voice_app_id: str) -> VoiceAppResource:
        """
        Asynchronously retrieve a single voice app by its id.
        """
        res = await self.client.request(
            "GET",
            self.paths["retrieve"].format(voice_app_id),
        )
        return cast(
            VoiceAppResource,
            self.resource(unwrap_data(res.json())),
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
        """
        Asynchronously update a voice app by its id.
        """
        validate_webhook_api_version(webhook_api_version)
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
            self.resource(unwrap_data(res.json())),
        )

    async def delete(self, voice_app_id: str) -> DeleteResult:
        """
        Asynchronously delete a voice app by its id.
        """
        res = await self.client.request(
            "DELETE",
            self.paths["delete"].format(voice_app_id),
        )
        return DeleteResult(unwrap_data(res.json()))

    async def list_virtual_numbers(
        self,
        voice_app_id: str,
        search: Optional[str] = None,
        location: Optional[List[str]] = None,
        limit: int = 10,
        cursor_after: Optional[str] = None,
        cursor_before: Optional[str] = None,
    ) -> CursorPage:
        """
        Asynchronously list the virtual numbers assigned to a voice app.
        """
        params = build_params(
            search=search,
            location=location,
            limit=limit,
            cursor_after=cursor_after,
            cursor_before=cursor_before,
            max_limit=50,
        )
        res = await self.client.request(
            "GET",
            self.paths["virtual_numbers"].format(voice_app_id),
            params=params,
        )
        return to_cursor_page(res.json(), VirtualNumberResource)