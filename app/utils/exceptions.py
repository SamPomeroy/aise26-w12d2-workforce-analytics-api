from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """raised when authentication fails"""
    def __init__(self, detail: str = "could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionDeniedError(HTTPException):
    """raised when user lacks required permissions"""
    def __init__(self, detail: str = "permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundError(HTTPException):
    """raised when resource is not found"""
    def __init__(self, detail: str = "resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ValidationError(HTTPException):
    """raised when input validation fails"""
    def __init__(self, detail: str = "validation error"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class RateLimitError(HTTPException):
    """raised when rate limit is exceeded"""
    def __init__(self, detail: str = "rate limit exceeded", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)},
        )
