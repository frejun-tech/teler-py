import asyncio
import contextlib
from unittest.mock import patch

import pytest

from teler import exceptions
from teler.streams import StreamConnector, StreamOp, StreamType


# ---------------------------------------------------------------------------
# Fakes
#
# `bridge_stream` drives two `async for` loops: `call_ws.iter_text()` and the
# remote socket itself. An AsyncMock cannot stand in for either — calling an
# AsyncMock returns a coroutine, and `async for` cannot iterate a coroutine, so
# the loop body silently never runs and the coroutine is discarded ("coroutine
# was never awaited"). These fakes are real async iterables, so the relay logic
# is actually executed.
#
# One side is always given `hang=True`. `bridge_stream` waits on FIRST_COMPLETED,
# so if both sides finish immediately whichever wins is a race; hanging one side
# makes the outcome deterministic and also exercises the pending-task cancellation.
# ---------------------------------------------------------------------------

class FakeCallWS:
    """Stands in for the inbound call websocket."""

    def __init__(self, messages=(), hang=False):
        self._messages = list(messages)
        self._hang = hang
        self.sent_text = []
        self.closed_with = None

    def iter_text(self):
        return self._stream()

    async def _stream(self):
        if self._hang:
            await asyncio.Event().wait()
        for message in self._messages:
            yield message

    async def send_text(self, data):
        self.sent_text.append(data)

    async def close(self, code=None, reason=None):
        self.closed_with = (code, reason)


class FakeRemoteWS:
    """Stands in for the remote websocket, which is iterated directly."""

    def __init__(self, messages=(), hang=False):
        self._messages = list(messages)
        self._hang = hang
        self.sent = []

    def __aiter__(self):
        return self._stream()

    async def _stream(self):
        if self._hang:
            await asyncio.Event().wait()
        for message in self._messages:
            yield message

    async def send(self, data):
        self.sent.append(data)


@contextlib.contextmanager
def patched_connect(remote_ws):
    with patch("websockets.connect") as mock_connect:
        mock_connect.return_value.__aenter__.return_value = remote_ws
        yield mock_connect


async def run_bridge(connector, call_ws, remote_ws, timeout=2.0):
    """Run the bridge, failing loudly if it does not settle."""
    with patched_connect(remote_ws) as mock_connect:
        await asyncio.wait_for(connector.bridge_stream(call_ws), timeout)
        return mock_connect


class TestStreamConnector:
    """Test cases for StreamConnector class."""

    def test_init_with_valid_parameters(self):
        """Test StreamConnector initialization with valid parameters."""
        remote_url = "ws://example.com/stream"
        connector = StreamConnector(
            stream_type=StreamType.BIDIRECTIONAL,
            remote_url=remote_url
        )

        assert connector.stream_type == StreamType.BIDIRECTIONAL
        assert connector.remote_url == remote_url
        # Test that handlers are set (don't compare static methods directly)
        assert connector.call_stream_handler is not None
        assert connector.remote_stream_handler is not None

    def test_init_with_custom_handlers(self):
        """Test StreamConnector initialization with custom handlers."""
        async def custom_handler(message: str):
            return (f"processed_{message}", StreamOp.RELAY)

        remote_url = "ws://example.com/stream"
        connector = StreamConnector(
            remote_url=remote_url,
            call_stream_handler=custom_handler,
            remote_stream_handler=custom_handler
        )

        assert connector.call_stream_handler == custom_handler
        assert connector.remote_stream_handler == custom_handler

    def test_init_missing_remote_url_raises_exception(self):
        """Test that initialization without remote_url raises BadParametersException."""
        with pytest.raises(exceptions.BadParametersException) as exc_info:
            StreamConnector(remote_url="")

        assert exc_info.value.param == "remote_url"
        assert "remote_url is a required parameter" in str(exc_info.value)

    def test_init_unidirectional_stream_raises_exception(self):
        """Test that unidirectional streams raise NotImplemented exception."""
        with pytest.raises(exceptions.NotImplementedException) as exc_info:
            StreamConnector(
                stream_type=StreamType.UNIDIRECTIONAL,
                remote_url="ws://example.com/stream"
            )

        assert "Unidirectional streams are not supported yet" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_default_stream_handler(self):
        """Test the default stream handler returns message with RELAY operation."""
        result = await StreamConnector._default_stream_handler("test_message")

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "test_message"
        assert result[1] == StreamOp.RELAY

    @pytest.mark.asyncio
    async def test_bridge_stream_establishes_websocket_connection(self):
        """Test that bridge_stream establishes WebSocket connection."""
        remote_url = "ws://example.com/stream"
        connector = StreamConnector(remote_url=remote_url)

        mock_connect = await run_bridge(
            connector, FakeCallWS(), FakeRemoteWS(hang=True)
        )

        mock_connect.assert_called_once_with(remote_url)

    @pytest.mark.asyncio
    async def test_bridge_stream_websocket_connection_error(self):
        """Test handling of WebSocket connection errors."""
        remote_url = "ws://example.com/stream"
        connector = StreamConnector(remote_url=remote_url)

        with patch('websockets.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception) as exc_info:
                await connector.bridge_stream(FakeCallWS())

            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_bridge_stream_relays_call_messages_to_remote(self):
        """A call-stream message the handler marks RELAY is forwarded to remote."""
        connector = StreamConnector(remote_url="ws://example.com/stream")
        call_ws = FakeCallWS(messages=["hello", "world"])
        remote_ws = FakeRemoteWS(hang=True)

        await run_bridge(connector, call_ws, remote_ws)

        assert remote_ws.sent == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_bridge_stream_relays_remote_messages_to_call(self):
        """A remote message the handler marks RELAY is forwarded to the call."""
        connector = StreamConnector(remote_url="ws://example.com/stream")
        call_ws = FakeCallWS(hang=True)
        remote_ws = FakeRemoteWS(messages=["from-remote"])

        await run_bridge(connector, call_ws, remote_ws)

        assert call_ws.sent_text == ["from-remote"]

    @pytest.mark.asyncio
    async def test_bridge_stream_applies_custom_handler_transform(self):
        """The handler's returned payload is what gets relayed, not the input."""
        async def prefixing_handler(message: str):
            return (f"processed_{message}", StreamOp.RELAY)

        connector = StreamConnector(
            remote_url="ws://example.com/stream",
            call_stream_handler=prefixing_handler,
        )
        remote_ws = FakeRemoteWS(hang=True)

        await run_bridge(connector, FakeCallWS(messages=["abc"]), remote_ws)

        assert remote_ws.sent == ["processed_abc"]

    @pytest.mark.asyncio
    async def test_bridge_stream_stop_closes_the_call_socket(self):
        """STOP from the call handler closes the call socket with code 1000."""
        async def stopping_handler(message: str):
            return (message, StreamOp.STOP)

        connector = StreamConnector(
            remote_url="ws://example.com/stream",
            call_stream_handler=stopping_handler,
        )
        call_ws = FakeCallWS(messages=["bye", "never-seen"])

        await run_bridge(connector, call_ws, FakeRemoteWS(hang=True))

        assert call_ws.closed_with == (1000, "Stream stopped by client")

    @pytest.mark.asyncio
    async def test_bridge_stream_stop_halts_further_relaying(self):
        """STOP breaks the loop, so messages after it are not relayed."""
        async def stop_on_second(message: str):
            if message == "stop":
                return (message, StreamOp.STOP)
            return (message, StreamOp.RELAY)

        connector = StreamConnector(
            remote_url="ws://example.com/stream",
            call_stream_handler=stop_on_second,
        )
        remote_ws = FakeRemoteWS(hang=True)

        await run_bridge(
            connector,
            FakeCallWS(messages=["first", "stop", "third"]),
            remote_ws,
        )

        assert remote_ws.sent == ["first"]

    @pytest.mark.asyncio
    async def test_bridge_stream_cleanup_on_completion(self):
        """The hanging side is cancelled once the other finishes.

        `run_bridge` wraps the call in `wait_for`, so if the pending task were
        not cancelled this would raise TimeoutError rather than return.
        """
        connector = StreamConnector(remote_url="ws://example.com/stream")

        await run_bridge(connector, FakeCallWS(), FakeRemoteWS(hang=True))
        await run_bridge(connector, FakeCallWS(hang=True), FakeRemoteWS())
