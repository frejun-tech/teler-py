import pytest

from teler import CallFlow

PLAY_ACTION = {"action": "play", "media_url": "https://example.com/hold.mp3"}
HANGUP_ACTION = {"action": "hangup"}


# --- stream ---
def test_stream_defaults():
    assert CallFlow.stream("wss://example.com/audio") == {
        "action": "stream",
        "ws_url": "wss://example.com/audio",
        "sample_rate": "8k",
        "chunk_size": 400,
        "record": True,
    }


def test_stream_overrides():
    flow = CallFlow.stream(
        "wss://example.com/audio",
        sample_rate="16k",
        chunk_size=800,
        record=False,
    )

    assert flow["sample_rate"] == "16k"
    assert flow["chunk_size"] == 800
    assert flow["record"] is False


def test_stream_options_are_keyword_only():
    with pytest.raises(TypeError):
        CallFlow.stream("wss://example.com/audio", 800)


# --- play ---
def test_play_omits_flow_url_when_unset():
    assert CallFlow.play("https://example.com/a.mp3") == {
        "action": "play",
        "media_url": "https://example.com/a.mp3",
    }


def test_play_includes_flow_url_when_given():
    flow = CallFlow.play("https://example.com/a.mp3", "https://example.com/next")

    assert flow["flow_url"] == "https://example.com/next"


# --- hangup ---
def test_hangup():
    assert CallFlow.hangup() == {"action": "hangup"}


# --- dial ---
def test_dial_defaults():
    assert CallFlow.dial("+15550001111") == {
        "action": "dial",
        "to": "+15550001111",
        "timeout": 30,
        "record": False,
        "ringback": "passthrough",
    }


def test_dial_accepts_a_sip_uri():
    assert CallFlow.dial("sip:user@host")["to"] == "sip:user@host"


def test_dial_omits_every_unset_optional():
    flow = CallFlow.dial("+15550001111")

    for key in (
        "custom_headers",
        "status_callback_url",
        "dial_music",
        "confirm_sound",
        "on_no_answer",
        "on_busy",
        "on_failure",
    ):
        assert key not in flow


def test_dial_maps_every_supported_field():
    flow = CallFlow.dial(
        "+15550001111",
        timeout=60,
        record="per_leg",
        custom_headers={"X-Trace": "t1"},
        status_callback_url="https://example.com/hook",
        ringback="suppress",
        dial_music=PLAY_ACTION,
        confirm_sound=PLAY_ACTION,
        on_no_answer=HANGUP_ACTION,
        on_busy=HANGUP_ACTION,
        on_failure=PLAY_ACTION,
    )

    assert flow == {
        "action": "dial",
        "to": "+15550001111",
        "timeout": 60,
        "record": "per_leg",
        "custom_headers": {"X-Trace": "t1"},
        "status_callback_url": "https://example.com/hook",
        "ringback": "suppress",
        "dial_music": PLAY_ACTION,
        "confirm_sound": PLAY_ACTION,
        "on_no_answer": HANGUP_ACTION,
        "on_busy": HANGUP_ACTION,
        "on_failure": PLAY_ACTION,
    }


def test_dial_options_are_keyword_only():
    with pytest.raises(TypeError):
        CallFlow.dial("+15550001111", 60)


def test_dial_no_longer_accepts_the_old_number_pair():
    with pytest.raises(TypeError):
        CallFlow.dial(from_number="+15550001111", to_number="+15550002222")
