from typing import Any, Optional


class TelerException(Exception):
    message = "An exception occurred."
    code = 500

    def __init__(
        self,
        msg: str = "",
        details: Any = None,
        code: Optional[int] = None,
    ):
        self.message = msg or self.message
        self.details = details
        self.code = code if code is not None else self.code
        super().__init__(self.message)


class BadParametersException(TelerException):
    message = "Bad Parameter(s)."
    code = 400

    def __init__(
        self,
        param: str = "",
        msg: str = "",
        details: Any = None,
        code: Optional[int] = None,
    ):
        self.param = param
        super().__init__(
            msg=msg or self.message,
            details=details,
            code=code,
        )


class UnauthorizedException(TelerException):
    message = "Unauthorized."
    code = 401


class ForbiddenException(TelerException):
    message = "Forbidden."
    code = 403


class NotFoundException(TelerException):
    message = "Not found."
    code = 404


class ConflictException(TelerException):
    message = "Resource Conflict."
    code = 409


class GoneException(TelerException):
    message = "Resource is no longer available."
    code = 410


class UnprocessableRequestException(TelerException):
    message = "Unprocessable Request."
    code = 422


class RateLimitException(TelerException):
    message = "Rate limit reached."
    code = 429


class InternalServerErrorException(TelerException):
    message = "Internal Server Error."
    code = 500


class NotImplementedException(TelerException):
    message = "Not implemented."
    code = 501