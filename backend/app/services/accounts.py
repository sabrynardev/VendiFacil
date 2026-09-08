from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.account import Account
from app.models.category import Category
from app.models.user import User, UserRole
from app.services.profiles import ensure_default_profiles

DEFAULT_ACCOUNT_CATEGORIES = [
    "Bebidas",
    "Alimentos",
    "Limpeza",
    "Higiene",
    "Frios",
    "Padaria",
    "Hortifruti",
    "Doces",
    "Outros",
]


def ensure_default_categories(db: Session, account_id: int) -> None:
    existing_names = {
        name
        for (name,) in db.query(Category.name).filter(Category.account_id == account_id).all()
    }
    for name in DEFAULT_ACCOUNT_CATEGORIES:
        if name not in existing_names:
            db.add(
                Category(
                    account_id=account_id,
                    name=name,
                    description=f"Categoria {name}",
                )
            )


def create_account_with_admin(
    db: Session,
    account_name: str,
    admin_name: str,
    admin_email: str,
    password: str,
    *,
    with_default_categories: bool = True,
) -> User:
    account = Account(name=account_name, active=True)
    db.add(account)
    db.flush()

    profiles = ensure_default_profiles(db, account.id)

    admin = User(
        account_id=account.id,
        profile_id=profiles[UserRole.ADMIN.value].id,
        name=admin_name,
        email=admin_email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        active=True,
    )
    db.add(admin)

    if with_default_categories:
        ensure_default_categories(db, account.id)

    db.commit()
    db.refresh(admin)
    return admin
