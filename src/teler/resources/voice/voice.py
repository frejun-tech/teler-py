from typing import Any

from teler.resources.voice import AsyncCallResourceManager, CallResourceManager, AsyncAppResourceManager, AppResourceManager, AsyncMutationResourceManager, MutationResourceManager, AsyncOperationResourceManager, OperationResourceManager


class VoiceResourceManager:
    """Synchronous aggregator for all voice-related resource managers."""

    def __init__(self, client: Any):
        self.apps = AppResourceManager(client)
        self.calls = CallResourceManager(client)
        self.mutations = MutationResourceManager(client)
        self.operations = OperationResourceManager(client)


class AsyncVoiceResourceManager:
    """Asynchronous aggregator for all voice-related resource managers."""

    def __init__(self, client: Any):
        self.apps = AsyncAppResourceManager(client)
        self.calls = AsyncCallResourceManager(client)
        self.mutations = AsyncMutationResourceManager(client)
        self.operations = AsyncOperationResourceManager(client)