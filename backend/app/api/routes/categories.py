from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.audit import log_audit

router = APIRouter()


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_VIEW))):
    return (
        db.query(Category)
        .filter(Category.account_id == current_user.account_id)
        .order_by(Category.name.asc())
        .all()
    )


def ensure_unique_name(db: Session, account_id: int, name: str, exclude_id: int | None = None) -> None:
    query = db.query(Category).filter(Category.account_id == account_id, func.lower(Category.name) == name.lower())
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Já existe uma categoria com esse nome.")


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    ensure_unique_name(db, current_user.account_id, payload.name)
    category = Category(account_id=current_user.account_id, **payload.model_dump())
    db.add(category)
    db.flush()
    log_audit(db, current_user, action="CREATE", entity_type="CATEGORY", entity_id=category.id, description=f"Criou a categoria {category.name}.")
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    category = db.query(Category).filter(Category.id == category_id, Category.account_id == current_user.account_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    ensure_unique_name(db, current_user.account_id, payload.name, category.id)
    before = {"name": category.name, "description": category.description}
    category.name = payload.name
    category.description = payload.description
    log_audit(db, current_user, action="UPDATE", entity_type="CATEGORY", entity_id=category.id, description=f"Atualizou a categoria {category.name}.", changes={"before": before, "after": payload.model_dump()})
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    category = db.query(Category).filter(Category.id == category_id, Category.account_id == current_user.account_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    if category.products:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta categoria possui produtos vinculados e não pode ser excluída.")
    name = category.name
    category_id_value = category.id
    db.delete(category)
    log_audit(db, current_user, action="DELETE", entity_type="CATEGORY", entity_id=category_id_value, description=f"Excluiu a categoria {name}.")
    db.commit()
