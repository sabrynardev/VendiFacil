from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import SaleCreate, SaleItemResponse, SaleResponse
from app.services.sales import SaleValidationError, create_sale

router = APIRouter()


def serialize_sale(sale: Sale) -> SaleResponse:
    return SaleResponse(
        id=sale.id,
        user_id=sale.user_id,
        operator_name=sale.user.name,
        subtotal=float(sale.subtotal),
        discount=float(sale.discount),
        total=float(sale.total),
        payment_method=sale.payment_method,
        amount_received=float(sale.amount_received) if sale.amount_received is not None else None,
        change_amount=float(sale.change_amount) if sale.change_amount is not None else None,
        status=sale.status,
        created_at=sale.created_at,
        items=[
            SaleItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=float(item.quantity),
                unit_price=float(item.unit_price),
                discount=float(item.discount),
                subtotal=float(item.subtotal),
            )
            for item in sale.items
        ],
    )


@router.get("", response_model=list[SaleResponse])
def list_sales(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sales = db.query(Sale).filter(Sale.account_id == current_user.account_id).order_by(Sale.created_at.desc()).all()
    return [serialize_sale(sale) for sale in sales]


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.account_id == current_user.account_id).first()
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada.")
    return serialize_sale(sale)


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale_endpoint(payload: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        sale = create_sale(db, payload, current_user)
    except SaleValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return serialize_sale(sale)
