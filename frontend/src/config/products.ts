export const PRODUCT_UNITS = [
  { value: "UN", label: "Unidade" },
  { value: "KG", label: "Quilograma (kg)" },
  { value: "G", label: "Grama (g)" },
  { value: "L", label: "Litro" },
  { value: "ML", label: "Mililitro (ml)" },
] as const;

export function calculateMargin(costPrice: number, salePrice: number) {
  const margin = salePrice - costPrice;
  return {
    margin,
    percent: salePrice > 0 ? (margin / salePrice) * 100 : 0,
  };
}
