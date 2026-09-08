import { useEffect, useState } from "react";
import type { Category, Product, Supplier } from "../types";
import { Button } from "./Button";

interface Props {
  categories: Category[];
  suppliers: Supplier[];
  initialValue?: Product | null;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
  onCancel: () => void;
}

type ProductFormState = {
  name: string;
  description: string;
  sku: string;
  barcode: string;
  category_id: string | number;
  supplier_id: string | number;
  cost_price: number;
  sale_price: number;
  stock_quantity: number;
  minimum_stock: number;
  unit: string;
  active: boolean;
};

const defaultState: ProductFormState = {
  name: "",
  description: "",
  sku: "",
  barcode: "",
  category_id: "",
  supplier_id: "",
  cost_price: 0,
  sale_price: 0,
  stock_quantity: 0,
  minimum_stock: 0,
  unit: "unidade",
  active: true,
};

export function ProductForm({ categories, suppliers, initialValue, onSubmit, onCancel }: Props) {
  const [form, setForm] = useState<ProductFormState>(defaultState);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialValue) {
      setForm({
        name: initialValue.name,
        description: initialValue.description ?? "",
        sku: initialValue.sku,
        barcode: initialValue.barcode ?? "",
        category_id: initialValue.category_id ?? "",
        supplier_id: initialValue.supplier_id ?? "",
        cost_price: initialValue.cost_price,
        sale_price: initialValue.sale_price,
        stock_quantity: initialValue.stock_quantity,
        minimum_stock: initialValue.minimum_stock,
        unit: initialValue.unit,
        active: initialValue.active,
      });
    } else {
      setForm(defaultState);
    }
  }, [initialValue]);

  const margin = Number(form.sale_price) - Number(form.cost_price);
  const marginPercent = Number(form.cost_price) > 0 ? (margin / Number(form.cost_price)) * 100 : 0;

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    await onSubmit({
      ...form,
      category_id: form.category_id || null,
      supplier_id: form.supplier_id || null,
      cost_price: Number(form.cost_price),
      sale_price: Number(form.sale_price),
      stock_quantity: Number(form.stock_quantity),
      minimum_stock: Number(form.minimum_stock),
    });
    setSaving(false);
  }

  return (
    <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
      {[
        { name: "name", label: "Nome" },
        { name: "sku", label: "SKU" },
        { name: "barcode", label: "Código de barras" },
        { name: "unit", label: "Unidade" },
      ].map((field) => (
        <label key={field.name} className="space-y-2 text-sm">
          <span className="text-slate-600">{field.label}</span>
          <input
            required={field.name !== "barcode"}
            className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
            value={String((form as Record<string, string | number | boolean>)[field.name] ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, [field.name]: event.target.value }))}
          />
        </label>
      ))}

      <label className="space-y-2 text-sm md:col-span-2">
        <span className="text-slate-600">Descrição</span>
        <textarea
          className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
          rows={3}
          value={form.description}
          onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
        />
      </label>

      <label className="space-y-2 text-sm">
        <span className="text-slate-600">Categoria</span>
        <select
          className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
          value={String(form.category_id)}
          onChange={(event) => setForm((current) => ({ ...current, category_id: event.target.value }))}
        >
          <option value="">Selecione</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </label>

      <label className="space-y-2 text-sm">
        <span className="text-slate-600">Fornecedor</span>
        <select
          className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
          value={String(form.supplier_id)}
          onChange={(event) => setForm((current) => ({ ...current, supplier_id: event.target.value }))}
        >
          <option value="">Selecione</option>
          {suppliers.map((supplier) => (
            <option key={supplier.id} value={supplier.id}>
              {supplier.name}
            </option>
          ))}
        </select>
      </label>

      {[
        { name: "cost_price", label: "Preço de custo" },
        { name: "sale_price", label: "Preço de venda" },
        { name: "stock_quantity", label: "Estoque inicial" },
        { name: "minimum_stock", label: "Estoque mínimo" },
      ].map((field) => (
        <label key={field.name} className="space-y-2 text-sm">
          <span className="text-slate-600">{field.label}</span>
          <input
            type="number"
            min="0"
            step="0.01"
            className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
            value={(form as Record<string, string | number | boolean>)[field.name] as number}
            onChange={(event) => setForm((current) => ({ ...current, [field.name]: Number(event.target.value) }))}
          />
        </label>
      ))}

      <div className="rounded-2xl border border-stroke bg-brand/4 p-4 text-sm md:col-span-2">
        <p>Margem: <span className="font-semibold text-brandStrong">{margin.toFixed(2)}</span></p>
        <p className="mt-1">Percentual: <span className="font-semibold text-brand">{marginPercent.toFixed(2)}%</span></p>
      </div>

      <div className="flex items-center justify-end gap-3 md:col-span-2">
        <Button type="button" variant="ghost" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={saving}>
          {saving ? "Salvando..." : "Salvar produto"}
        </Button>
      </div>
    </form>
  );
}
