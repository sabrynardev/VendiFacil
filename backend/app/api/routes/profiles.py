from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.profile import Profile
from app.models.user import User
from app.schemas.profile import ProfileResponse

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
