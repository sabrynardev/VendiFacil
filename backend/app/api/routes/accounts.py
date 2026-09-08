from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import create_access_token
from app.database.session import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountRegisterRequest
from app.schemas.auth import TokenResponse
from app.services.accounts import create_account_with_admin

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_account(payload: AccountRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Account).filter(Account.name == payload.account_name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma conta com esse nome.")

    if db.query(User).filter(User.email == payload.admin_email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail.")

    admin = create_account_with_admin(
        db,
        account_name=payload.account_name,
        admin_name=payload.admin_name,
        admin_email=payload.admin_email,
        password=payload.password,
        with_default_categories=payload.with_default_categories,
    )
    token = create_access_token(admin.email)
    return TokenResponse(access_token=token)
