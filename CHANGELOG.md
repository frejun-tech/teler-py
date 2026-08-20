# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-08-20

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
- `teler.__version__`.

### Changed

- Arguments the API rejects are now validated client-side and raise
  `BadParametersException` before the request is sent, rather than surfacing as an
  HTTP error. This covers pagination (`limit` outside 1–100, both cursors at once),
  SIP trunk authentication pairing, virtual number selection and assignment
  targets, and IP ACL addresses. **Code that caught the HTTP 400 for these cases
  must now catch `BadParametersException`.**
- `respx` moved from the runtime dependencies to the `test` extra. It is a test-only
  mocking library and was never imported at runtime.

### Fixed

- **Recordings returned the wrong URL.** The retrieve path carried a trailing slash,
  so the API answered with a redirect and the SDK returned the Teler API URL instead
  of the signed storage URL.
- **SIP trunks and voice apps raised `TypeError` against current backends.**
  `SipTrunkResource` now declares `ip_acl_id`, `ip_acl_name` and `code`, and
  `VoiceAppResource` declares `code`; previously any response carrying them failed,
  because resources reject undeclared fields.
- The asynchronous `update` in the base resource manager never awaited its request,
  returning a coroutine where a resource was expected.
- `VirtualNumberResource` was defined twice; the voice types module now imports the
  canonical one.
- Asynchronous `transfer` type hints were narrower than the synchronous signature.

## [0.2.2] - 2026-07-24

- Version-only release.

## [0.2.1] - 2026-07-24

### Fixed

- The `dial` call flow emitted the key `from_numebr` instead of `from_number`.
