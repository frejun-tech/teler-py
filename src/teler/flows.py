from typing import Any, Dict, Optional, Union


class CallFlow:
    """Builders for the call flow actions served from a flow URL."""

    @staticmethod
    def stream(
        ws_url: str,
        *,
        sample_rate: str = "8k",
        chunk_size: int = 400,
        record: bool = True,
    ) -> Dict[str, Any]:
        """
        Build and return stream action flow.

        Opens a bidirectional WebSocket carrying real-time call audio to
        ``ws_url``.
        """
        return {
            "action": "stream",
            "ws_url": ws_url,
            "sample_rate": sample_rate,
            "chunk_size": chunk_size,
            "record": record,
        }

    @staticmethod
    def play(media_url: str, flow_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Build and return play action flow.

        Plays a single audio file into the call. ``flow_url`` requests the next
        flow from that URL once playback finishes (beta).
        """
        payload: Dict[str, Any] = {"action": "play", "media_url": media_url}
        if flow_url is not None:
            payload["flow_url"] = flow_url
        return payload

    @staticmethod
    def hangup() -> Dict[str, Any]:
        """
        Build and return hangup action flow.

        Ends the call immediately.
        """
        return {"action": "hangup"}

    @staticmethod
    def dial(
        to: str,
        *,
        timeout: int = 30,
        record: Union[bool, str] = False,
        custom_headers: Optional[Dict[str, str]] = None,
        status_callback_url: Optional[str] = None,
        ringback: str = "passthrough",
        dial_music: Optional[Dict[str, Any]] = None,
        confirm_sound: Optional[Dict[str, Any]] = None,
        on_no_answer: Optional[Dict[str, Any]] = None,
        on_busy: Optional[Dict[str, Any]] = None,
        on_failure: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build and return dial action flow.

        Originates an outbound leg from an in-progress call and bridges it once
        the target answers. Requires the owning voice app to be pinned to
        webhook version ``2026-06-01``.

        ``to`` is an E.164 phone number or a SIP URI (``sip:user@host``), one
        target only. ``timeout`` is 1..600 seconds. ``record`` is ``False``,
        ``True``, ``"stereo"``, ``"mono"`` or ``"per_leg"``. ``custom_headers``
        keys must start with ``X-``, at most 16 headers with values up to 256
        bytes. ``ringback`` is ``"passthrough"`` or ``"suppress"``.

        ``dial_music``, ``confirm_sound``, ``on_no_answer``, ``on_busy`` and
        ``on_failure`` each take a nested action, either
        ``{"action": "play", "media_url": ..., "loop": ...}`` or
        ``{"action": "hangup"}``.
        """
        payload: Dict[str, Any] = {
            "action": "dial",
            "to": to,
            "timeout": timeout,
            "record": record,
        }
        if custom_headers is not None:
            payload["custom_headers"] = custom_headers
        if status_callback_url is not None:
            payload["status_callback_url"] = status_callback_url
        payload["ringback"] = ringback
        optional = (
            ("dial_music", dial_music),
            ("confirm_sound", confirm_sound),
            ("on_no_answer", on_no_answer),
            ("on_busy", on_busy),
            ("on_failure", on_failure),
        )
        for key, value in optional:
            if value is not None:
                payload[key] = value
        return payload
