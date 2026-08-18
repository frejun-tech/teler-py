import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from teler.resources.base import (AsyncBaseResourceManager, BaseResource,
                                  BaseResourceManager)

PATHS: Dict[str, str] = {
    "create": "/voice/calls/initiate"
}

@dataclass
class CallResource(BaseResource):
    """Represents a call resource returned by the Teler API."""
    id: str
    from_number: Optional[str]
    to_number: Optional[str]
    status: Optional[str]
    status_callback_url: Optional[str]
    record: Optional[bool]
    created_at: Optional[str]
    updated_at: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


class CallResourceManager(BaseResourceManager):
    """Synchronous manager for call resources."""
    def __init__(self, client: Any):
        super().__init__(client, CallResource, PATHS)

    def create(
        self,
        from_number: str,
        to_number: str,
        flow_url: str,
        status_callback_url: str,
        record: bool = True,
    ) -> CallResource:
        """
        Create a new call resource.
        """
        data = {
            "from_number": from_number,
            "to_number": to_number,
            "flow_url": flow_url,
            "status_callback_url": status_callback_url,
            "record": record,
        }
        res = self.client.request("POST", self.paths["create"], data=json.dumps(data))
        return cast(CallResource, self.resource(res.json()['data']))


class AsyncCallResourceManager(AsyncBaseResourceManager):
    """Asynchronous manager for call resources."""
    def __init__(self, client: Any):
        super().__init__(client, CallResource, PATHS)

    async def create(
        self,
        from_number: str,
        to_number: str,
        flow_url: str,
        status_callback_url: str,
        record: bool = True,
    ) -> CallResource:
        """
        Asynchronously create a new call resource.
        """
        data = {
            "from_number": from_number,
            "to_number": to_number,
            "flow_url": flow_url,
            "status_callback_url": status_callback_url,
            "record": record,
        }
        res = await self.client.request("POST", self.paths["create"], data=json.dumps(data))
        return cast(CallResource, self.resource(res.json()['data']))
