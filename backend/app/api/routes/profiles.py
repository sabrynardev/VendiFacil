from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.profile import Permission, Profile
from app.models.user import User
from app.schemas.profile import ProfilePermissionsUpdate, ProfileResponse
from app.services.audit import log_audit

router = APIRouter()


@router.get("", response_model=list[ProfileResponse])
def list_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_MANAGE)),
):
    return (
        db.query(Profile)
        .filter(Profile.account_id == current_user.account_id, Profile.active.is_(True))
        .order_by(Profile.name.asc())
        .all()
    )


@router.put("/{profile_id}/permissions", response_model=ProfileResponse)
def update_profile_permissions(
    profile_id: int,
    payload: ProfilePermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USERS_MANAGE)),
):
    profile = db.query(Profile).filter(Profile.id == profile_id, Profile.account_id == current_user.account_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    if profile.code == "ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="As permissões do Administrador são protegidas.")

    requested_codes = set(payload.permission_codes)
    permissions = db.query(Permission).filter(Permission.code.in_(requested_codes)).all()
    found_codes = {permission.code for permission in permissions}
    invalid_codes = sorted(requested_codes - found_codes)
    if invalid_codes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Permissões inválidas: {', '.join(invalid_codes)}.")

    before = sorted(permission.code for permission in profile.permissions)
    profile.permissions = permissions
    after = sorted(found_codes)
    log_audit(
        db,
        current_user,
        action="UPDATE_PERMISSIONS",
        entity_type="PROFILE",
        entity_id=profile.id,
        description=f"Atualizou as permissões do perfil {profile.name}.",
        changes={"before": before, "after": after},
    )
    db.commit()
    db.refresh(profile)
    return profile
