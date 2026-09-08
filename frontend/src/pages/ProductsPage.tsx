import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { ProductForm } from "../components/ProductForm";
import { useToast } from "../components/ToastProvider";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import type { Product } from "../types";
import { formatCurrency } from "../utils/format";

export function ProductsPage() {
  const toast = useToast();
  const { data, loading, setData } = useAsync(async () => {
    const [products, categories, suppliers] = await Promise.all([
      catalogService.listProducts(),
      catalogService.listCategories(),
      catalogService.listSuppliers(),
    ]);
    return { products, categories, suppliers };
  }, []);
  const [editing, setEditing] = useState<Product | null>(null);
  const [open, setOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function refresh() {
    const products = await catalogService.listProducts();
    setData((current) => (current ? { ...current, products } : current));
  }

  async function handleSubmit(payload: Record<string, unknown>) {
    if (editing) {
      await catalogService.updateProduct(editing.id, payload);
      toast.push("Produto atualizado com sucesso.");
    } else {
      await catalogService.createProduct(payload);
      toast.push("Produto criado com sucesso.");
    }
    await refresh();
    setOpen(false);
    setEditing(null);
  }

  async function handleDelete(product: Product) {
    if (!window.confirm(`Excluir o produto "${product.name}"?`)) return;
    setDeletingId(product.id);
    try {
      await catalogService.deleteProduct(product.id);
      setData((current) => current ? { ...current, products: current.products.filter((item) => item.id !== product.id) } : current);
      toast.push("Produto removido com sucesso.", "success");
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível excluir o produto.", "error");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="page-title">Produtos</h1>
          <p className="page-subtitle">Cadastro com preço, margem, fornecedor e status automático de estoque.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} className="mr-2" />
          Novo produto
        </Button>
      </div>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-500">Carregando produtos...</p>
        ) : data.products.length === 0 ? (
          <EmptyState title="Nenhum produto cadastrado" description="Cadastre o primeiro item para começar a vender." />
        ) : (
          <DataTable headers={["Nome", "Marca", "SKU", "Categoria", "Custo", "Venda", "Margem", "Estoque", "Status", "Ações"]}>
            {data.products.map((product) => (
              <tr key={product.id}>
                <td className="px-4 py-3">
                  <div>
                    <p className="font-medium">{product.name}</p>
                    <p className="text-xs text-slate-500">{product.barcode || "Sem código"}</p>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">{product.brand || "Sem marca"}</td>
                <td className="px-4 py-3 text-slate-600">{product.sku}</td>
                <td className="px-4 py-3 text-slate-600">{product.category_name || "Sem categoria"}</td>
                <td className="px-4 py-3">{formatCurrency(product.cost_price)}</td>
                <td className="px-4 py-3">{formatCurrency(product.sale_price)}</td>
                <td className="px-4 py-3 text-brandStrong">{formatCurrency(product.margin)}</td>
                <td className="px-4 py-3">{product.stock_quantity}</td>
                <td className="px-4 py-3">
                  <Badge label={product.stock_status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => { setEditing(product); setOpen(true); }}>
                      <Pencil size={16} />
                    </Button>
                    <Button variant="ghost" disabled={deletingId === product.id} onClick={() => handleDelete(product)}>
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>

      {open && data && (
        <Modal title={editing ? "Editar produto" : "Novo produto"} onClose={() => { setOpen(false); setEditing(null); }}>
          <ProductForm
            categories={data.categories}
            suppliers={data.suppliers}
            initialValue={editing}
            onCancel={() => { setOpen(false); setEditing(null); }}
            onSubmit={handleSubmit}
          />
        </Modal>
      )}
    </div>
  );
}
