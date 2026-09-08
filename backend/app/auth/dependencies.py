from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.user import User, UserRole
from app.services.profiles import permission_codes_for_user

oauth2_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.")

    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido.")
    if not user.account or not user.account.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Conta inválida.")
    return user


def require_roles(*roles: UserRole):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado.")
        return user

    return dependency


def require_permission(permission: PermissionCode):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if permission.value not in permission_codes_for_user(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não possui permissão para esta ação.")
        return user

    return dependency


def require_any_permission(*permissions: PermissionCode):
    def dependency(user: User = Depends(get_current_user)) -> User:
        user_permissions = set(permission_codes_for_user(user))
        if not any(permission.value in user_permissions for permission in permissions):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Você não possui permissão para esta área.")
        return user

    return dependency
