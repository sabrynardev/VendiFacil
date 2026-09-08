from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.security import hash_password
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.audit import log_audit
from app.services.profiles import profile_for_role

router = APIRouter()


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        profile_name=user.profile.name if user.profile else user.role.value.title(),
        active=user.active,
        created_at=user.created_at,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_MANAGE)),
):
    users = db.query(User).filter(User.account_id == current_user.account_id).order_by(User.name.asc()).all()
    return [serialize_user(user) for user in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_MANAGE)),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail.")

    profile = profile_for_role(db, current_user.account_id, payload.role)
    user = User(
        account_id=current_user.account_id,
        profile_id=profile.id,
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=payload.active,
    )
    db.add(user)
    db.flush()
    log_audit(
        db,
        current_user,
        action="CREATE",
        entity_type="USER",
        entity_id=user.id,
        description=f"Criou o usuário {user.name} com perfil {profile.name}.",
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_MANAGE)),
):
    user = db.query(User).filter(User.id == user_id, User.account_id == current_user.account_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if user.id == current_user.id and (not payload.active or payload.role != current_user.role):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Você não pode desativar ou alterar o próprio perfil.")
    duplicate = db.query(User).filter(User.email == payload.email, User.id != user.id).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe um usuário com esse e-mail.")

    before = {"name": user.name, "email": user.email, "role": user.role.value, "active": user.active}
    profile = profile_for_role(db, current_user.account_id, payload.role)
    user.name = payload.name
    user.email = payload.email
    user.role = payload.role
    user.profile_id = profile.id
    user.active = payload.active
    if payload.password:
        user.password_hash = hash_password(payload.password)
    after = {"name": user.name, "email": user.email, "role": user.role.value, "active": user.active}
    log_audit(
        db,
        current_user,
        action="UPDATE",
        entity_type="USER",
        entity_id=user.id,
        description=f"Atualizou o usuário {user.name}.",
        changes={"before": before, "after": after},
    )
    db.commit()
    db.refresh(user)
    return serialize_user(user)
