# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-04

### Added

- **Idempotency support for call initiation and call control.**
  `client.voice.calls.create`, `client.voice.mutations.*` and
  `client.voice.operations.transfer` accept optional `idempotency_key`, `retry`
  and `base_retry_delay_ms` arguments.
  - A UUID v4 is generated when `idempotency_key` is omitted.
  - Keys are validated client-side: non-empty and at most 255 characters.
    Invalid keys raise `BadParametersException` before the request is sent.
  - `retry` enables retries on network errors and HTTP 429/503 responses for that
    request.

- **Configurable API base URL.** `TELER_BACKEND_DOMAIN` sets the scheme and host
  for the whole process; the SDK appends `/api/v1`. A `base_url` argument to
  `Client` or `AsyncClient` takes precedence.

- **Remote WebSocket headers.** `StreamConnector` accepts `remote_headers`, a
  mapping of extra HTTP headers sent with the WebSocket handshake to
  `remote_url` — for example an `Authorization` bearer token or ElevenLabs'
  `xi-api-key`.

### Changed

- `GET` and `DELETE` requests retry by default (three retries, 100 ms base
  delay). `POST` and `PATCH` remain opt-in.
- Retries use exponential backoff with full jitter, capped at 2000 ms, unless the
  response carries a `Retry-After` header.
- Call initiation and call-control requests use a 5-second timeout and a 300 ms
  base retry delay.
- `websockets>=14.0` is now required (was `>=10.0`); `StreamConnector` uses the
  `additional_headers` handshake argument.

### Removed

- **`webhook_api_version="2025-08-01"` is no longer accepted.** Only
  `2026-06-01` is supported. Passing the retired version raises
  `BadParametersException` before the request is sent. Migrate existing voice
  apps and SIP trunks:

  ```python
  client.voice.apps.update(app_id, webhook_api_version="2026-06-01")
  client.sip.trunks.update(trunk_id, webhook_api_version="2026-06-01")
  ```

  New resources already default to `2026-06-01`.

### Fixed

- **The `Retry-After` response header was never read.** The retry loop looked for
  it inside the exception's `details`, which holds the API's `errors` array, so a
  429/503 response always fell back to the computed backoff. Both clients now read
  the header from the response.

### Documentation

- Rewrote `README.md` to match the Node SDK's structure while describing the
  Python SDK's actual behavior: installation, features, client configuration,
  field naming, pagination, call initiation with idempotency, call flows, call
  controls, media streaming, logging, and error handling.
- Fixed the async example, which was missing a colon, did not import `asyncio`,
  and never closed the client.
- Fixed stream-handler examples that returned `{}` for `StreamOp.PASS` instead of
  an empty string.
- Corrected `tests/contract/README.md`: `BaseResource` ignores undeclared response
  keys and keeps the full body on `.raw`; it no longer raises `TypeError`.

## [1.0.0] - 2026-09-18

Completes the SDK's coverage of the public API: every non-deprecated operation in
the OpenAPI schema is now implemented, synchronous and asynchronous.

**This release contains breaking changes.** It is also required for compatibility
with backends that return the SIP trunk IP ACL fields — see *Fixed* below.

### Removed

- **`client.calls` has been removed. Use `client.voice.calls`.** The method
  signature is unchanged, so this is a namespace move:

  ```python
  # before
  call = client.calls.create(from_number=..., to_number=..., flow_url=..., ...)
  # after
  call = client.voice.calls.create(from_number=..., to_number=..., flow_url=..., ...)
  ```

- The `teler.resources.calls` module, superseded by `teler.resources.voice.calls`.
- The `teler.base_client` module, which was unreferenced.

### Added

- `client.virtual_numbers` — list with filters, assign and unassign against a voice
  app or SIP trunk, and update.
- `client.sip.trunks` — full CRUD, including listing a trunk's virtual numbers.
- `client.sip.calls` — list and retrieve.
- `client.sip.ip_acls` — full CRUD for named IP access control lists that trunks can
  authorise against, as an alternative to inline addresses.
- `client.secrets` — full CRUD for webhook signing secrets, including rotation.
- `ip_acl_id` on SIP trunk create and update. With `authentication_type="IP"`,
  supply exactly one of `auth_addresses` or `ip_acl_id`.
- `GoneException`, raised on HTTP 410 — needed for event redelivery.
- `transport` on SIP trunk create and update: `"tls"`, `"tcp"` or `"udp"`.
  `"udp"` is only accepted with `authentication_type="credential"`.
- `CallFlow.hangup()`, which ends the call immediately.
- `flow_url` on `CallFlow.play`, requesting the next flow from that URL once
  playback finishes (beta), and `sample_rate` on `CallFlow.stream`.
- `py.typed`, so type checkers see the SDK's annotations instead of treating it as
  untyped.
- `requires-python = ">=3.9"`, so pip refuses the install on older interpreters
  rather than failing at import.
- `teler.__version__`.

### Changed

- **`CallFlow.dial` now matches the current API.** The single-target shape replaces
  the caller-supplied leg numbers, and the remaining arguments are keyword-only:

  ```python
  # before
  CallFlow.dial(from_number=..., to_number=..., status_callback_url=..., record=True)
  # after
  CallFlow.dial(to=..., timeout=30, record=False, status_callback_url=...)
  ```

  `to` is one E.164 number or SIP URI. `record` widens to `False`, `True`,
  `"stereo"`, `"mono"` or `"per_leg"`, and now defaults to `False`. Added along
  with it: `custom_headers`, `ringback`, `dial_music`, `confirm_sound`,
  `on_no_answer`, `on_busy` and `on_failure`. The action requires the owning voice
  app to be pinned to webhook version `2026-06-01`.
- **`CallFlow.play` emits `media_url`, not `file_url`**, and takes its argument
  under that name. The old key was rejected by the API.
- `CallFlow.stream` takes `chunk_size` and `record` as keyword-only arguments.
  **Positional calls must be updated.**
- **Resources ignore response keys they do not declare.** Previously any
  undeclared key raised `TypeError`, so a field added by the API broke every call
  returning that resource until the SDK caught up. The full response body is kept
  on `.raw`.
- Headers passed to the client constructor now override the SDK defaults, matched
  case-insensitively, so a custom `User-Agent`, `Accept` or `Content-Type` reaches
  the API. `x-api-key` is still always taken from the validated `api_key` argument
  and cannot be displaced by a header.
- `webhook_api_version` on `client.sip.trunks.create` and
  `client.voice.apps.create` now defaults to `2026-06-01` instead of being left
  unset. An unset field is stored as `2025-08-01` by the API, so a create that
  did not name a version produced a trunk or app on the older payload. Pass the
  argument explicitly to choose a different accepted version.
- `webhook_api_version` on `client.sip.trunks.update` and
  `client.voice.apps.update` is sent only when supplied, so an update that does
  not name a version leaves the stored one alone rather than migrating it.
- `webhook_api_version` is validated client-side against the versions the API
  accepts (`2025-08-01`, `2026-06-01`) and raises `BadParametersException`.
- Arguments the API rejects are now validated client-side and raise
  `BadParametersException` before the request is sent, rather than surfacing as an
  HTTP error. This covers pagination (`limit` outside 1–100, both cursors at once),
  SIP trunk authentication pairing, `transport="udp"` without credential
  authentication, virtual number selection and assignment targets, and IP ACL
  addresses — including networks broader than `/24` (IPv4) or `/64` (IPv6) and
  loopback or unspecified addresses, which are not usable SIP sources. **Code that
  caught the HTTP 400 for these cases must now catch `BadParametersException`.**
- SIP trunk `update` enforces its own auth rules, which differ from `create`:
  `authentication_type` is required alongside any of `auth_credential`,
  `auth_addresses` or `ip_acl_id`, and an empty `auth_addresses` list is rejected.
- SIP trunk `auth_addresses` entries take a single IP address. A CIDR network is
  rejected — use `client.sip.ip_acls` for a range, which does accept one.
- `respx` moved from the runtime dependencies to the `test` extra. It is a test-only
  mocking library and was never imported at runtime.

### Fixed

- **Recordings returned the wrong URL.** The retrieve path carried a trailing slash,
  so the API answered with a redirect and the SDK returned the Teler API URL instead
  of the signed storage URL.
- **SIP trunks and voice apps raised `TypeError` against current backends.**
  `SipTrunkResource` now declares `ip_acl_id`, `ip_acl_name` and `code`, and
  `VoiceAppResource` declares `code`. Responses carrying keys the SDK still does
  not declare no longer fail at all — see *Changed*.
- The asynchronous `update` in the base resource manager never awaited its request,
  returning a coroutine where a resource was expected.
- `VirtualNumberResource` was defined twice; the voice types module now imports the
  canonical one.
- Asynchronous `transfer` type hints were narrower than the synchronous signature.
- `code` on exceptions was annotated `int` while defaulting to `None`, and
  `details` was left untyped; they are now `Optional[int]` and `Any`.
- `secret_value` no longer appears in the secret resource's `repr`, so logging or
  printing a secret does not disclose it.

## [0.2.2] - 2026-07-24

- Version-only release.

## [0.2.1] - 2026-07-24

### Fixed

- The `dial` call flow emitted the key `from_numebr` instead of `from_number`.
