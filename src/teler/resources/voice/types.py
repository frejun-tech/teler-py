from typing import Any, Dict, Optional
from dataclasses import dataclass

from teler.resources.base import BaseResource
from teler.resources.virtual_numbers import VirtualNumberResource  # noqa: F401


@dataclass
class CallResource(BaseResource):
    id: str
    account_id: Optional[str]
    voice_app_id: Optional[str]
    state: Optional[str]
    direction: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    properties: Optional[Dict[str, Any]]
    created_at: Optional[str]
    answered_at: Optional[str]
    ended_at: Optional[str]
    reason: Optional[str]
    legs: Optional[list]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class CallLegResource(BaseResource):
    id: str
    call_session_id: Optional[str]
    direction: Optional[str]
    role: Optional[str]
    state: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    parent_leg_id: Optional[str]
    recordings: Optional[list]
    created_at: Optional[str]
    answered_at: Optional[str]
    ended_at: Optional[str]
    reason: Optional[str]
    ended_by: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class CreateCallResource(BaseResource):
    id: str
    from_number: Optional[str]
    to_number: Optional[str]
    status_callback_url: Optional[str]
    record: Optional[bool]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class VoiceAppResource(BaseResource):
    id: str
    name: Optional[str]
    flow_url: Optional[str]
    webhook_url: Optional[str]
    fallback_url: Optional[str]
    status: Optional[str]
    channel_limit: Optional[int]
    vn_count: int
    secret_id: Optional[str]
    secret_name: Optional[str]
    webhook_api_version: Optional[str]
    account_id: Optional[str]
    code: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class DeleteResult(BaseResource):
    success: bool
    message: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class MutationResource(BaseResource):
    request_id: str
    playback_id: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class TransferResource(BaseResource):
    id: str
    call_id: str
    status: Optional[str]
    target_leg_id: Optional[str]
    mode: Optional[str]
    request_id: str

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
