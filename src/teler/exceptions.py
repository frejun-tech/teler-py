class TelerException(Exception):
    message = "An exception occurred."
    code = 500

    def __init__(self, msg: str = ""):
        super().__init__(msg or self.message)


class BadParametersException(TelerException):
    message = "Bad Parameter(s)."
    code = 400

    def __init__(self, param: str = "", msg: str = ""):
        self.param = param
        super().__init__(msg or self.message)


class UnauthorizedException(TelerException):
    message = "Unauthorized."
    code = 401


class ForbiddenException(TelerException):
    message = "Forbidden."
    code = 403


class NotFoundException(TelerException):
    message = "Not found."
    code = 404


class NotImplementedException(TelerException):
    message = "Not implemented."
    code = 501