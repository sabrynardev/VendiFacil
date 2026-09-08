from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum


class ProductUnit(StrEnum):
    UN = "UN"
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"


UNIT_LABELS = {
    ProductUnit.UN: "Unidade",
    ProductUnit.KG: "Quilograma (kg)",
    ProductUnit.G: "Grama (g)",
    ProductUnit.L: "Litro",
    ProductUnit.ML: "Mililitro (ml)",
}


def calculate_margin(cost_price: float | Decimal, sale_price: float | Decimal) -> tuple[float, float]:
    cost = Decimal(str(cost_price))
    sale = Decimal(str(sale_price))
    margin = (sale - cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    percent = Decimal("0") if sale == 0 else (margin / sale * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(margin), float(percent)
