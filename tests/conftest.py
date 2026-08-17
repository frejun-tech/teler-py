"""Shared collection helpers for both test directories.

``sdk_paths`` enumerates every endpoint the SDK can request. Both the hermetic
well-formedness checks in ``tests/unit`` and the live routing checks in
``tests/contract`` parametrize over it, so a new resource is covered by both the
moment its ``PATHS`` dict exists.
"""
import importlib

import pytest

RESOURCE_MODULES = [
    "teler.resources.events",
    "teler.resources.recordings",
    "teler.resources.secrets",
    "teler.resources.virtual_numbers",
    "teler.resources.sip.calls",
    "teler.resources.sip.trunks",
    "teler.resources.voice.calls",
    "teler.resources.voice.apps",
    "teler.resources.voice.mutations",
    "teler.resources.voice.operations",
]


def sdk_paths():
    """(module, key, path template) for every path the SDK can request."""
    out = []
    for name in RESOURCE_MODULES:
        paths = getattr(importlib.import_module(name), "PATHS", {})
        for key, template in sorted(paths.items()):
            out.append((name.replace("teler.resources.", ""), key, template))
    return out


def pytest_generate_tests(metafunc):
    if "sdk_path" in metafunc.fixturenames:
        cases = sdk_paths()
        metafunc.parametrize(
            "sdk_path", cases, ids=[f"{m}.{k}" for m, k, _ in cases]
        )


@pytest.fixture(scope="session")
def all_sdk_paths():
    """The whole path list at once, for tests that sweep rather than parametrize.

    A fixture rather than an import because ``tests/`` is not a package, so
    subdirectories cannot import this module directly.
    """
    return sdk_paths()
