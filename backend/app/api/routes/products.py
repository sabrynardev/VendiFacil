from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.database.session import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.sale import SaleItem
from app.models.stock_movement import StockMovement
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


def serialize_product(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
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
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    products = (
        db.query(Product)
        .filter(Product.account_id == current_user.account_id, Product.active.is_(True))
        .order_by(Product.name.asc())
        .all()
    )
    return [serialize_product(product) for product in products]


@router.get("/barcode/{barcode}", response_model=ProductResponse)
def get_by_barcode(barcode: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
):
    validate_relationships(db, current_user.account_id, payload.category_id, payload.supplier_id)
    product = Product(account_id=current_user.account_id, **payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.account_id == current_user.account_id, Product.active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")
    validate_relationships(db, current_user.account_id, payload.category_id, payload.supplier_id)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return serialize_product(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.ESTOQUE)),
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
    db.commit()
