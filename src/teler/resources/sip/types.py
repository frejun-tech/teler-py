from dataclasses import dataclass
from typing import Any, Dict, Optional

from teler.resources.base import BaseResource


@dataclass
class SipCallResource(BaseResource):
    """Represents a SIP call session returned by the Teler API."""
    id: str
    account_id: Optional[str]
    sip_trunk_id: Optional[str]
    state: Optional[str]
    direction: Optional[str]
    from_number: Optional[str]
    to_number: Optional[str]
    created_at: Optional[str]
    answered_at: Optional[str]
    ended_at: Optional[str]
    duration_seconds: Optional[int]
    reason: Optional[str]
    ended_by: Optional[str]
    recordings: Optional[list]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class SipTrunkResource(BaseResource):
    """Represents a SIP trunk returned by the Teler API."""
    id: str
    name: Optional[str]
    domain_name: Optional[str]
    account_id: Optional[str]
    channel_limit: Optional[int]
    cps_limit: Optional[int]
    recording_enabled: Optional[bool]
    secure: Optional[bool]
    is_active: Optional[bool]
    auth_ip_addresses: Optional[list]
    auth_credential_usernames: Optional[list]
    ip_acl_id: Optional[str]
    ip_acl_name: Optional[str]
    sip_route: Optional[Dict[str, Any]]
    webhook_url: Optional[str]
    webhook_api_version: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    secret_id: Optional[str]
    secret_name: Optional[str]
    code: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class IpAclResource(BaseResource):
    """Represents a SIP IP access control list returned by the Teler API.

    The list and detail endpoints return different shapes, so this declares the
    union of both. ``addresses`` and ``updated_at`` are populated by create,
    retrieve and update; ``address_count`` only by list. Whichever the response
    omits reads back as ``None``.
    """
    id: str
    name: Optional[str]
    addresses: Optional[list]
    address_count: Optional[int]
    trunk_count: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)


@dataclass
class DeleteResult(BaseResource):
    """Result of a SIP trunk delete request."""
    success: bool
    message: Optional[str]

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
