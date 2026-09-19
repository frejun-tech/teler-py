"""Well-formedness of every endpoint path the SDK requests.

Hermetic — no backend needed. A trailing slash here is not cosmetic: the API
answers a slash-normalising redirect instead of routing, which is how
``recordings.retrieve()`` came to return the Teler API's own URL in place of a
signed S3 URL. The live counterpart is tests/contract/test_live_routing.py.
"""


def test_path_is_absolute(sdk_path):
    module, key, template = sdk_path
    assert template.startswith("/"), f"{module}.{key} is not absolute: {template}"


def test_path_has_no_trailing_slash(sdk_path):
    module, key, template = sdk_path
    assert not template.endswith("/"), (
        f"{module}.{key} has a trailing slash ({template}); the API would answer "
        "a redirect instead of routing to the handler"
    )


def test_path_has_no_double_slash(sdk_path):
    module, key, template = sdk_path
    assert "//" not in template, f"{module}.{key} has a double slash: {template}"


def test_placeholders_are_positional(sdk_path):
    """Paths are filled with str.format(), so braces must be bare `{}`."""
    module, key, template = sdk_path
    for fragment in template.split("/"):
        if fragment.startswith("{"):
            assert fragment == "{}", (
                f"{module}.{key} uses a named placeholder {fragment!r}; "
                "PATHS templates are filled positionally with .format()"
            )
