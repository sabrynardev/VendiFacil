from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.session import get_db
from app.models.supplier import Supplier
from app.models.user import UserRole
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate

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
        created_at=supplier.created_at,
        products_count=len(supplier.products),
    )


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    return [serialize_supplier(supplier) for supplier in suppliers]


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
):
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return serialize_supplier(supplier)


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    for field, value in payload.model_dump().items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return serialize_supplier(supplier)


@router.delete("/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")
    db.delete(supplier)
    db.commit()
