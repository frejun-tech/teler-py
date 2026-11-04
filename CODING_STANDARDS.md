# Teler Python SDK Coding Standards

This document outlines the coding standards and best practices for the `teler-sdk-py` codebase. All contributors must adhere to these guidelines to ensure code quality, maintainability, and consistency.

---

## 1. **General Style**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style and formatting.
- Use 4 spaces per indentation level.
- Limit lines to 100 characters.
- Use descriptive variable, function, and class names.
- Avoid abbreviations unless they are well-known (e.g., `id`, `url`).

## 2. **Imports**
- Group imports in the following order: standard library, third-party, local imports.
- Remove unused imports.
- Use absolute imports for modules within the package.
- For type annotations that would cause circular imports, use `from typing import TYPE_CHECKING` and string-based annotations or `Any`.

## 3. **Class and Method Structure**
- Each public class and method must have a clear, concise docstring describing its purpose and usage.
- Use type annotations for all function/method parameters and return types.
- Use `@dataclass` for simple data containers.
- Resource managers should be instantiated in the client classes and exposed as attributes (e.g., `client.voice.calls`).
- Public API names use `snake_case` to match the API wire format; no key conversion is performed.
- Use `Any` or string-based type annotations for cross-module references that could cause circular imports.

## 4. **Error Handling**
- Raise SDK-specific exceptions (e.g., `BadParametersException`) for invalid parameters or configuration.
- Do not expose raw HTTPX exceptions to users; wrap or document them as needed.
- Validate all required parameters at the earliest opportunity.

## 5. **Resource and Manager Design**
- All resource classes must inherit from `BaseResource` and use `@dataclass`.
- All resource managers must inherit from `BaseResourceManager` or `AsyncBaseResourceManager`.
- Use `cast()` from `typing` when returning a more specific resource type from a generic manager.
- Document all public methods.

## 6. **Testing**
- All new features and bug fixes must include appropriate unit and (if applicable) integration tests.
- Use `pytest` for all tests.
- Use `respx` for mocking HTTP requests in both sync and async tests.
- Ensure both sync and async code paths are tested.
- Keep test coverage high and avoid skipping tests without justification.

## 7. **Async vs Sync**
- Never mix sync and async code in the same class or method.
- All async resource managers and methods must be clearly marked and separated from sync ones.

## 8. **Configuration**
- Allow overriding the API base URL and headers via constructor arguments.
- Support environment variable configuration for API keys and base URLs if possible.

## 9. **Documentation**
- All public classes, methods, and modules must have docstrings.
- Keep the README up to date with usage examples for both sync and async clients.
- Document all exceptions that can be raised by public methods.
- Keep the README section structure aligned with the Node SDK (`teler-sdk-node`):
  What is Teler, Requirements, Features, Installation, Basic Usage, Client
  Configuration, Resources, Field Naming, Pagination, Call Initiation with
  Idempotency, Call Flows, Call Controls & Mutations, Media Streaming, Logging,
  Error Handling.
- Describe what the Python SDK actually does. Do not copy Node-only behavior
  (camelCase conversion, auto-pagination, injectable loggers, heartbeat handling)
  into the Python documentation.
- Document idempotency and retry arguments (`idempotency_key`, `retry`,
  `base_retry_delay_ms`) wherever a public method accepts them.

## 10. **Deprecation and Backward Compatibility**
- Mark deprecated methods/classes clearly in the docstring and with warnings if possible.
- Avoid breaking changes unless absolutely necessary; document any breaking changes in the changelog.

---

**All code contributions must pass linting, type checking, and the full test suite before merging.** 