"""Voice transfers and call-control mutations, driven against the real API.

Both route families hand their work to ``run_mutation``, so that is the
function these tests patch — the action dict it receives is the payload after
the real request models have parsed it.
"""
import pytest

from teler import exceptions
from teler.resources.voice.types import MutationResource, TransferResource

from .harness import fake_mutation, fake_transfer

OPERATIONS = "app.api.routes.public.v1.voice.operations"
MUTATIONS = "app.api.routes.public.v1.voice.mutations"

CALL_ID = "cs_01JQ8Z9K7M3N2P4R5S6T7V8W9X"
PSTN_TARGET = {"kind": "pstn", "number": "+14155559876"}
MEDIA_URL = "https://example.com/audio/greeting.wav"


@pytest.fixture
def capture_transfer(patch_crud):
    """Patch run_mutation under the transfer route and record what it receives."""
    captured = {}

    async def _run(*, request, db, account, call_id, leg_id, action,
                   extra_response=None, pre_exec=None, compensate_on_error=None):
        captured["action"] = action
        captured["call_id"] = call_id
        return fake_transfer(
            call_id=call_id,
            mode=action["mode"],
            transfer_id=action["transfer_id"],
        )

    patch_crud(f"{OPERATIONS}.run_mutation", _run)
    return captured


@pytest.fixture
def capture_mutation(patch_crud):
    """Patch run_mutation under the hangup/mute/dtmf/play routes."""
    captured = {}

    async def _run(*, request, db, account, call_id, leg_id, action,
                   extra_response=None, pre_exec=None, compensate_on_error=None):
        captured["action"] = action
        captured["call_id"] = call_id
        return fake_mutation(with_playback=action["type"] == "play")

    patch_crud(f"{MUTATIONS}.run_mutation", _run)
    return captured


# ------------------------------ transfer -------------------------------

def test_transfer_to_a_pstn_target(client, capture_transfer):
    transfer = client.voice.operations.transfer(
        CALL_ID, target=PSTN_TARGET, mode="cold"
    )

    # The SDK payload satisfied TransferRequest, which sets extra="forbid".
    action = capture_transfer["action"]
    assert capture_transfer["call_id"] == CALL_ID
    assert action["mode"] == "cold"
    assert action["target"] == PSTN_TARGET
    assert action["timeout"] == 30
    assert isinstance(transfer, TransferResource)
    assert transfer.id.startswith("op_")
    assert transfer.call_id == CALL_ID
    assert transfer.status == "initiated"
    assert transfer.mode == "cold"


def test_transfer_with_a_nested_dial_music_action(client, capture_transfer):
    """TransferNestedAction sets extra="forbid", so the key must be `action`."""
    transfer = client.voice.operations.transfer(
        CALL_ID,
        target=PSTN_TARGET,
        mode="cold",
        dial_music={"action": "play", "media_url": MEDIA_URL, "loop": True},
        timeout=45,
    )

    action = capture_transfer["action"]
    assert action["dial_music"] == {
        "action": "play",
        "media_url": MEDIA_URL,
        "loop": True,
    }
    assert action["timeout"] == 45
    assert isinstance(transfer, TransferResource)


def test_transfer_mode_bridge_rejected_by_the_real_literal(client, capture_transfer):
    with pytest.raises(exceptions.UnprocessableRequestException) as excinfo:
        client.voice.operations.transfer(CALL_ID, target=PSTN_TARGET, mode="bridge")

    assert excinfo.value.code == 422
    assert "action" not in capture_transfer


def test_transfer_mode_warm_rejected_by_the_route_gate(client, capture_transfer):
    """`warm` is in the Literal but not in _SUPPORTED_TRANSFER_MODES."""
    with pytest.raises(exceptions.BadParametersException) as excinfo:
        client.voice.operations.transfer(CALL_ID, target=PSTN_TARGET, mode="warm")

    assert excinfo.value.code == 400
    assert "action" not in capture_transfer


def test_transfer_target_kind_number_rejected_by_the_real_literal(client, capture_transfer):
    with pytest.raises(exceptions.UnprocessableRequestException) as excinfo:
        client.voice.operations.transfer(
            CALL_ID, target={"kind": "number", "number": "+14155559876"}, mode="cold"
        )

    assert excinfo.value.code == 422
    assert "action" not in capture_transfer


# ------------------------------ mutations ------------------------------

def test_play_with_on_dtmf_ignore(client, capture_mutation):
    result = client.voice.mutations.play(
        CALL_ID, media_url=MEDIA_URL, on_dtmf="ignore", loop=3
    )

    action = capture_mutation["action"]
    assert action["on_dtmf"] == "ignore"
    assert action["media_url"] == MEDIA_URL
    assert action["loop"] == 3
    assert action["playback_id"].startswith("pb_")
    assert isinstance(result, MutationResource)
    assert result.playback_id.startswith("pb_")


def test_play_with_on_dtmf_continue_rejected_by_the_real_literal(client, capture_mutation):
    with pytest.raises(exceptions.UnprocessableRequestException) as excinfo:
        client.voice.mutations.play(CALL_ID, media_url=MEDIA_URL, on_dtmf="continue")

    assert excinfo.value.code == 422
    assert "action" not in capture_mutation


def test_hangup_with_an_uppercase_reason(client, capture_mutation):
    result = client.voice.mutations.hangup(CALL_ID, reason="NORMAL_CLEARING")

    assert capture_mutation["action"] == {
        "type": "hangup",
        "reason": "NORMAL_CLEARING",
    }
    assert isinstance(result, MutationResource)
    assert result.request_id.startswith("req_")
    assert result.playback_id is None


def test_hangup_with_a_lowercase_reason_rejected_by_the_real_pattern(client, capture_mutation):
    """HangupRequest.reason is constrained to ^[A-Z0-9_]+$."""
    with pytest.raises(exceptions.UnprocessableRequestException) as excinfo:
        client.voice.mutations.hangup(CALL_ID, reason="normal_clearing")

    assert excinfo.value.code == 422
    assert "action" not in capture_mutation
