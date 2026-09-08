from sqlalchemy.orm import Session

from app.core.permissions import DEFAULT_PROFILE_PERMISSIONS, PERMISSION_LABELS, PermissionCode
from app.models.profile import Permission, Profile
from app.models.user import User, UserRole


PROFILE_NAMES = {
    "ADMIN": "Administrador",
    "GERENTE": "Gerente",
    "CAIXA": "Caixa",
    "ESTOQUE": "Estoque",
}


def ensure_permissions(db: Session) -> dict[str, Permission]:
    existing = {permission.code: permission for permission in db.query(Permission).all()}
    for code, (name, module) in PERMISSION_LABELS.items():
        if code.value not in existing:
            permission = Permission(code=code.value, name=name, module=module)
            db.add(permission)
            existing[code.value] = permission
    db.flush()
    return existing


def ensure_default_profiles(db: Session, account_id: int) -> dict[str, Profile]:
    permissions = ensure_permissions(db)
    profiles = {
        profile.code: profile
        for profile in db.query(Profile).filter(Profile.account_id == account_id).all()
    }
    for code, permission_codes in DEFAULT_PROFILE_PERMISSIONS.items():
        profile = profiles.get(code)
        if not profile:
            profile = Profile(
                account_id=account_id,
                name=PROFILE_NAMES[code],
                code=code,
                active=True,
                is_system=True,
            )
            db.add(profile)
            profiles[code] = profile
        profile.permissions = [permissions[item.value] for item in permission_codes]
    db.flush()
    return profiles


def permission_codes_for_user(user: User) -> list[str]:
    if user.profile and user.profile.active:
        return sorted(permission.code for permission in user.profile.permissions)
    return sorted(permission.value for permission in DEFAULT_PROFILE_PERMISSIONS.get(user.role.value, []))


def profile_for_role(db: Session, account_id: int, role: UserRole) -> Profile:
    profiles = ensure_default_profiles(db, account_id)
    return profiles[role.value]


def backfill_account_profiles(db: Session) -> None:
    account_ids = [account_id for (account_id,) in db.query(User.account_id).distinct().all()]
    for account_id in account_ids:
        profiles = ensure_default_profiles(db, account_id)
        for user in db.query(User).filter(User.account_id == account_id, User.profile_id.is_(None)).all():
            user.profile_id = profiles[user.role.value].id
    db.commit()
