from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.models.user import User
from app.schemas.inventory import (
    InventoryRecord,
    StockAlert,
    StockMovementCreate,
    StockMovementResponse,
)
from app.services.audit import log_audit
from app.services.inventory import inventory_projection, product_status

router = APIRouter()


@router.get("", response_model=list[InventoryRecord])
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_VIEW)),
):
    records = []
    for product in (
        db.query(Product)
        .filter(Product.account_id == current_user.account_id, Product.active.is_(True))
        .order_by(Product.name.asc())
        .all()
    ):
        projection = inventory_projection(db, product, current_user.account_id)
        records.append(
            InventoryRecord(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                category_name=product.category.name if product.category else None,
                stock_quantity=float(product.stock_quantity),
                minimum_stock=float(product.minimum_stock),
                average_sales_per_day=projection["average_sales_per_day"],
                days_remaining=projection["days_remaining"],
                purchase_recommendation=projection["purchase_recommendation"],
                status=projection["status"],
            )
        )
    return records


@router.get("/alerts", response_model=list[StockAlert])
def alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_VIEW)),
):
    data = []
    for product in db.query(Product).filter(Product.account_id == current_user.account_id, Product.active.is_(True)).all():
        status_label = product_status(float(product.stock_quantity), float(product.minimum_stock))
        if status_label != "NORMAL":
            data.append(
                StockAlert(
                    product_id=product.id,
                    product_name=product.name,
                    stock_quantity=float(product.stock_quantity),
                    minimum_stock=float(product.minimum_stock),
                    status=status_label,
                )
            )
    return data


@router.get("/predictions", response_model=list[InventoryRecord])
def predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_VIEW)),
):
    return list_inventory(db, current_user)


@router.post("/movement", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def create_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_MANAGE)),
):
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.account_id == current_user.account_id, Product.active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado.")

    previous_stock = float(product.stock_quantity)
    delta = float(payload.quantity)
    if payload.type in {"perda", "venda"} and previous_stock < delta:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estoque insuficiente para a movimentação.")

    if payload.type in {"entrada", "devolucao"}:
        new_stock = previous_stock + delta
    else:
        new_stock = previous_stock - delta

    product.stock_quantity = new_stock
    movement = StockMovement(
        account_id=current_user.account_id,
        product_id=product.id,
        user_id=current_user.id,
        type=payload.type,
        quantity=delta,
        previous_stock=previous_stock,
        new_stock=new_stock,
        reason=payload.reason,
    )
    db.add(movement)
    log_audit(
        db,
        current_user,
        action="STOCK_MOVEMENT",
        entity_type="PRODUCT",
        entity_id=product.id,
        description=f"Registrou {payload.type} de {delta:g} em {product.name}.",
        changes={"before": previous_stock, "after": new_stock, "reason": payload.reason},
    )
    db.commit()
    db.refresh(movement)
    return StockMovementResponse(
        id=movement.id,
        product_name=product.name,
        quantity=float(movement.quantity),
        previous_stock=float(movement.previous_stock),
        new_stock=float(movement.new_stock),
        type=movement.type,
        user_name=current_user.name,
        reason=movement.reason,
        created_at=movement.created_at,
    )


@router.get("/movements", response_model=list[StockMovementResponse])
def list_movements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.INVENTORY_VIEW)),
):
    movements = (
        db.query(StockMovement)
        .filter(StockMovement.account_id == current_user.account_id)
        .order_by(StockMovement.created_at.desc())
        .all()
    )
    return [
        StockMovementResponse(
            id=movement.id,
            product_name=movement.product.name,
            quantity=float(movement.quantity),
            previous_stock=float(movement.previous_stock),
            new_stock=float(movement.new_stock),
            type=movement.type,
            user_name=movement.user.name if movement.user else None,
            reason=movement.reason,
            created_at=movement.created_at,
        )
        for movement in movements
    ]
