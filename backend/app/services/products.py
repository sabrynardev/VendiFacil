from sqlalchemy.orm import Session

from app.models.product import Product


class ProductConflictError(Exception):
    pass


def validate_unique_identifiers(
    db: Session,
    *,
    account_id: int,
    sku: str,
    barcode: str | None,
    exclude_product_id: int | None = None,
) -> None:
    sku_query = db.query(Product).filter(Product.account_id == account_id, Product.sku == sku)
    if exclude_product_id is not None:
        sku_query = sku_query.filter(Product.id != exclude_product_id)
    if sku_query.first():
        raise ProductConflictError(f'O SKU "{sku}" já está em uso por outro produto.')

    if barcode:
        barcode_query = db.query(Product).filter(Product.account_id == account_id, Product.barcode == barcode)
        if exclude_product_id is not None:
            barcode_query = barcode_query.filter(Product.id != exclude_product_id)
        if barcode_query.first():
            raise ProductConflictError(f'O código de barras "{barcode}" já está em uso por outro produto.')
