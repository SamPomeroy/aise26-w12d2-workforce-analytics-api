from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_access_token
from app.utils.exceptions import AuthenticationError, PermissionDeniedError

# http bearer token security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    validate jwt token and return current user
    raises 401 if token is invalid or user not found
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None or token_data.username is None:
        raise AuthenticationError("invalid authentication token")
    
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if user is None:
        raise AuthenticationError("user not found")
    
    if not user.is_active:
        raise AuthenticationError("user account is inactive")
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    ensure user is active
    useful for endpoints that require verified accounts
    """
    if not current_user.is_active:
        raise AuthenticationError("inactive user account")
    
    return current_user


def require_role(required_role: str):
    """
    dependency factory for role-based access control
    usage: Depends(require_role("admin"))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise PermissionDeniedError(
                f"this endpoint requires '{required_role}' role, you have '{current_user.role}'"
            )
        return current_user
    
    return role_checker


def require_roles(*allowed_roles: str):
    """
    dependency factory for multiple allowed roles
    usage: Depends(require_roles("admin", "employer"))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise PermissionDeniedError(
                f"this endpoint requires one of {allowed_roles}, you have '{current_user.role}'"
            )
        return current_user
    
    return role_checker


def optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    get current user if authenticated, otherwise return none
    useful for endpoints that work with or without auth
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        token_data = decode_access_token(token)
        
        if token_data is None or token_data.username is None:
            return None
        
        user = db.query(User).filter(User.username == token_data.username).first()
        return user if user and user.is_active else None
    except Exception:
        return None
