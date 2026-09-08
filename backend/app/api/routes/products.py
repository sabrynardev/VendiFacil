from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
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
from app.services.inventory import StockValidationError, apply_stock_movement
from app.services.products import ProductConflictError, validate_unique_identifiers

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
    search: str | None = Query(default=None, max_length=160),
    category_id: int | None = None,
    product_status: str = Query(default="active", alias="status", pattern="^(active|inactive|all)$"),
    low_stock: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission(PermissionCode.PRODUCTS_VIEW, PermissionCode.CASHIER_OPERATE)),
):
    query = db.query(Product).filter(Product.account_id == current_user.account_id)
    if product_status == "active":
        query = query.filter(Product.active.is_(True))
    elif product_status == "inactive":
        query = query.filter(Product.active.is_(False))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), Product.sku.ilike(term), Product.barcode.ilike(term)))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if low_stock:
        query = query.filter(Product.stock_quantity <= Product.minimum_stock)
    products = query.order_by(Product.name.asc()).all()
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
        .filter(Product.id == product_id, Product.account_id == current_user.account_id)
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
    try:
        validate_unique_identifiers(
            db, account_id=current_user.account_id, sku=payload.sku, barcode=payload.barcode
        )
    except ProductConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    product_data = payload.model_dump()
    initial_stock = float(product_data.pop("stock_quantity"))
    product = Product(account_id=current_user.account_id, stock_quantity=0, **product_data)
    db.add(product)
    db.flush()
    if initial_stock > 0:
        apply_stock_movement(
            db,
            product=product,
            user=current_user,
            movement_type=StockMovementType.ENTRADA,
            quantity=initial_stock,
            reason="Estoque inicial",
            reference_type="product",
            reference_id=product.id,
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
        .filter(Product.id == product_id, Product.account_id == current_user.account_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    validate_relationships(db, current_user.account_id, payload.category_id, payload.supplier_id)
    try:
        validate_unique_identifiers(
            db,
            account_id=current_user.account_id,
            sku=payload.sku,
            barcode=payload.barcode,
            exclude_product_id=product.id,
        )
    except ProductConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    tracked_fields = ["name", "brand", "sku", "barcode", "cost_price", "sale_price", "stock_quantity", "minimum_stock", "unit", "active"]
    before = {field: str(getattr(product, field)) for field in tracked_fields}
    previous_stock = float(product.stock_quantity)
    update_data = payload.model_dump()
    requested_stock = float(update_data.pop("stock_quantity"))
    for field, value in update_data.items():
        setattr(product, field, value)
    if previous_stock != requested_stock:
        try:
            apply_stock_movement(
                db,
                product=product,
                user=current_user,
                movement_type=StockMovementType.AJUSTE,
                quantity=abs(requested_stock - previous_stock),
                target_stock=requested_stock,
                reason="Alteração no cadastro do produto",
                reference_type="product",
                reference_id=product.id,
            )
        except StockValidationError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
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
