from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.audit import log_audit

router = APIRouter()


def serialize_supplier(supplier: Supplier) -> SupplierResponse:
    return SupplierResponse(
        id=supplier.id,
        name=supplier.name,
        cnpj=supplier.cnpj,
        phone=supplier.phone,
        whatsapp=supplier.whatsapp,
        email=supplier.email,
        address=supplier.address,
        notes=supplier.notes,
        active=supplier.active,
        created_at=supplier.created_at,
        products_count=len(supplier.products),
    )


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.SUPPLIERS_VIEW)),
):
    suppliers = (
        db.query(Supplier)
        .filter(Supplier.account_id == current_user.account_id, Supplier.active.is_(True))
        .order_by(Supplier.name.asc())
        .all()
    )
    return [serialize_supplier(supplier) for supplier in suppliers]


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.SUPPLIERS_MANAGE)),
):
    supplier = Supplier(account_id=current_user.account_id, **payload.model_dump())
    db.add(supplier)
    db.flush()
    log_audit(
        db,
        current_user,
        action="CREATE",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        description=f"Cadastrou o fornecedor {supplier.name}.",
    )
    db.commit()
    db.refresh(supplier)
    return serialize_supplier(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.SUPPLIERS_MANAGE)),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.account_id == current_user.account_id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    before = {"name": supplier.name, "phone": supplier.phone, "email": supplier.email, "active": supplier.active}
    for field, value in payload.model_dump().items():
        setattr(supplier, field, value)
    after = {"name": supplier.name, "phone": supplier.phone, "email": supplier.email, "active": supplier.active}
    log_audit(
        db,
        current_user,
        action="UPDATE",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        description=f"Atualizou o fornecedor {supplier.name}.",
        changes={"before": before, "after": after},
    )
    db.commit()
    db.refresh(supplier)
    return serialize_supplier(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.SUPPLIERS_MANAGE)),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.account_id == current_user.account_id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    has_products = bool(supplier.products)
    log_audit(
        db,
        current_user,
        action="ARCHIVE" if has_products else "DELETE",
        entity_type="SUPPLIER",
        entity_id=supplier.id,
        description=f"Removeu o fornecedor {supplier.name}.",
    )
    if has_products:
        supplier.active = False
    else:
        db.delete(supplier)
    db.commit()
