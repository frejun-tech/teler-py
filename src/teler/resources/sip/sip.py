from typing import Any

from teler.resources.sip import (
    AsyncSipCallResourceManager,
    SipCallResourceManager,
    AsyncSipTrunkResourceManager,
    SipTrunkResourceManager,
)


class SipResourceManager:
    """Synchronous aggregator for all SIP-related resource managers."""

    def __init__(self, client: Any):
        self.calls = SipCallResourceManager(client)
        self.trunks = SipTrunkResourceManager(client)


class AsyncSipResourceManager:
    """Asynchronous aggregator for all SIP-related resource managers."""

    def __init__(self, client: Any):
        self.calls = AsyncSipCallResourceManager(client)
        self.trunks = AsyncSipTrunkResourceManager(client)
