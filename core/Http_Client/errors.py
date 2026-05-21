class ApiError(Exception):
    pass


class UnauthorizedError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ServerError(ApiError):
    pass

class SessionReplacedError(UnauthorizedError):
    pass

class UnprocessableContentError(ApiError):
    pass

class MethodNotAllowedError(ApiError):
    pass

class ConflictError(ApiError):
    pass
