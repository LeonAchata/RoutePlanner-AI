class RouteError(Exception):
    """An error that should be shown to the user as-is.

    `status_code` is the HTTP status the API responds with: 422 for problems
    with what the user typed, 502 when an upstream API misbehaves.
    """

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UpstreamError(RouteError):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)
