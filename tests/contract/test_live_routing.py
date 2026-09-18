"""Every path the SDK requests must resolve on the real API's router.

The recordings defect was a path defect: the SDK asked for ``/recordings/`` while
the API serves ``/recordings``, so Starlette answered with a slash-normalising
redirect instead of the handler, and nothing failed loudly. These checks walk
every ``PATHS`` entry in the SDK against the live router, so a typo or stray
slash in any resource fails here instead of silently redirecting.

The hermetic half of this lives in tests/unit/test_resource_paths.py.
"""
import re

import httpx

# Satisfies the id-format checks that some routers run before touching the DB.
PLACEHOLDER = "cs_01JQ8Z9K7M3N2P4R5S6T7V8W9X"


def test_sdk_path_resolves_on_the_real_router(sdk_path, live_api):
    from starlette.routing import Match

    from .harness import build_app

    module, key, template = sdk_path
    full = "/api/v1" + template.replace("{}", PLACEHOLDER)

    best = Match.NONE
    for route in build_app().routes:
        match, _ = route.matches(
            {"type": "http", "path": full, "method": "GET", "headers": []}
        )
        if match.value > best.value:
            best = match

    # FULL means path and method matched; PARTIAL means the path matched but the
    # verb differs, which still proves the path itself is right.
    assert best in (Match.FULL, Match.PARTIAL), (
        f"{module}.{key} -> {full} matches no route on the real API"
    )


def test_no_sdk_path_triggers_a_slash_redirect(live_api, all_sdk_paths):
    redirected = []
    with httpx.Client(
        base_url=live_api.base_url,
        headers={"x-api-key": "test_api_key"},
        follow_redirects=False,
        timeout=10,
    ) as raw:
        for module, key, template in all_sdk_paths:
            path = template.replace("{}", PLACEHOLDER)
            res = raw.get(path)
            if 300 <= res.status_code < 400:
                redirected.append(
                    f"{module}.{key} {path} -> {res.status_code} "
                    f"{res.headers.get('location')}"
                )

    assert not redirected, (
        "SDK paths that redirect instead of routing:\n" + "\n".join(redirected)
    )


def test_every_sdk_path_appears_in_the_served_schema(live_api, all_sdk_paths):
    """Cross-check against the schema the API serves, not a saved copy."""
    from .harness import build_app

    served = {
        re.sub(r"\{[^}]+\}", "{}", p.replace("/api/v1", ""))
        for p in build_app().openapi()["paths"]
    }

    missing = [
        f"{module}.{key} -> {template}"
        for module, key, template in all_sdk_paths
        if template not in served
    ]
    assert not missing, (
        "SDK paths absent from the API schema:\n" + "\n".join(missing)
    )
