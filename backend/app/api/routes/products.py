from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_any_permission, require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.sale import SaleItem
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.audit import log_audit

router = APIRouter()


def serialize_product(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        description=product.description,
        sku=product.sku,
        barcode=product.barcode,
        category_id=product.category_id,
        supplier_id=product.supplier_id,
        cost_price=float(product.cost_price),
        sale_price=float(product.sale_price),
        stock_quantity=float(product.stock_quantity),
        minimum_stock=float(product.minimum_stock),
        unit=product.unit,
        active=product.active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        category_name=product.category.name if product.category else None,
        supplier_name=product.supplier.name if product.supplier else None,
    )


def validate_relationships(db: Session, account_id: int, category_id: int | None, supplier_id: int | None):
    if category_id and not db.query(Category).filter(Category.id == category_id, Category.account_id == account_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    if supplier_id and not db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.account_id == account_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")


@router.get("", response_model=list[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission(PermissionCode.PRODUCTS_VIEW, PermissionCode.CASHIER_OPERATE)),
):
    products = (
        db.query(Product)
        .filter(Product.account_id == current_user.account_id, Product.active.is_(True))
        .order_by(Product.name.asc())
        .all()
    )
    return [serialize_product(product) for product in products]


@router.get("/barcode/{barcode}", response_model=ProductResponse)
def get_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission(PermissionCode.PRODUCTS_VIEW, PermissionCode.CASHIER_OPERATE)),
):
    product = (
        db.query(Product)
        .filter(
            Product.account_id == current_user.account_id,
            Product.active.is_(True),
            (Product.barcode == barcode) | (Product.sku == barcode) | (Product.name.ilike(f"%{barcode}%")),
        )
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return serialize_product(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission(PermissionCode.PRODUCTS_VIEW, PermissionCode.CASHIER_OPERATE)),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.account_id == current_user.account_id, Product.active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    return serialize_product(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    validate_relationships(db, current_user.account_id, payload.category_id, payload.supplier_id)
    product = Product(account_id=current_user.account_id, **payload.model_dump())
    db.add(product)
    db.flush()
    if float(product.stock_quantity) > 0:
        db.add(
            StockMovement(
                account_id=current_user.account_id,
                product_id=product.id,
                user_id=current_user.id,
                type=StockMovementType.ENTRADA,
                quantity=float(product.stock_quantity),
                previous_stock=0,
                new_stock=float(product.stock_quantity),
                reason="Estoque inicial",
            )
        )
    log_audit(
        db,
        current_user,
        action="CREATE",
        entity_type="PRODUCT",
        entity_id=product.id,
        description=f"Cadastrou o produto {product.name}.",
    )
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.account_id == current_user.account_id, Product.active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    validate_relationships(db, current_user.account_id, payload.category_id, payload.supplier_id)
    tracked_fields = ["name", "brand", "sku", "barcode", "cost_price", "sale_price", "stock_quantity", "minimum_stock", "unit", "active"]
    before = {field: str(getattr(product, field)) for field in tracked_fields}
    previous_stock = float(product.stock_quantity)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    new_stock = float(product.stock_quantity)
    if previous_stock != new_stock:
        db.add(
            StockMovement(
                account_id=current_user.account_id,
                product_id=product.id,
                user_id=current_user.id,
                type=StockMovementType.AJUSTE,
                quantity=abs(new_stock - previous_stock),
                previous_stock=previous_stock,
                new_stock=new_stock,
                reason="Alteração no cadastro do produto",
            )
        )
    after = {field: str(getattr(product, field)) for field in tracked_fields}
    changes = {field: {"before": before[field], "after": after[field]} for field in tracked_fields if before[field] != after[field]}
    log_audit(
        db,
        current_user,
        action="UPDATE",
        entity_type="PRODUCT",
        entity_id=product.id,
        description=f"Atualizou o produto {product.name}.",
        changes=changes,
    )
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PRODUCTS_MANAGE)),
):
    product = db.query(Product).filter(Product.id == product_id, Product.account_id == current_user.account_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    has_history = (
        db.query(SaleItem.id).filter(SaleItem.product_id == product.id).first() is not None
        or db.query(StockMovement.id).filter(StockMovement.product_id == product.id).first() is not None
    )
    if has_history:
        product.active = False
    else:
        db.delete(product)
    log_audit(
        db,
        current_user,
        action="ARCHIVE" if has_history else "DELETE",
        entity_type="PRODUCT",
        entity_id=product.id,
        description=f"Removeu o produto {product.name}.",
    )
    db.commit()
