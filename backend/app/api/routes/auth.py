from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, verify_password
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import CurrentUserResponse, LoginRequest, TokenResponse
from app.services.profiles import permission_codes_for_user
from app.services.rate_limit import login_account_limiter, login_limiter

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_host = request.client.host if request.client else "unknown"
    limiter_key = client_host
    if not login_limiter.check(limiter_key, limit=20, interval_seconds=300):
        raise HTTPException(status_code=429, detail="Muitas tentativas de acesso. Aguarde alguns minutos.")
    user = db.query(User).filter(User.email == payload.email).first()
    account_key = payload.email.strip().casefold()
    if user and not login_account_limiter.check(account_key, limit=5, interval_seconds=300):
        raise HTTPException(status_code=429, detail="Muitas tentativas de acesso. Aguarde alguns minutos.")
    if not user or not user.active or not user.account or not user.account.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    login_limiter.clear(limiter_key)
    login_account_limiter.clear(account_key)
    token = create_access_token(user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)):
    return CurrentUserResponse(
        id=current_user.id,
        account_id=current_user.account_id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        active=current_user.active,
        created_at=current_user.created_at,
        account=current_user.account,
        profile_name=current_user.profile.name if current_user.profile else current_user.role.value.title(),
        permissions=permission_codes_for_user(current_user),
    )
