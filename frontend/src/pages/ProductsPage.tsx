import { Pencil, Plus, Trash2 } from "lucide-react";
import { useDeferredValue, useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { ProductForm } from "../components/ProductForm";
import { useToast } from "../components/ToastProvider";
import { useAuth } from "../contexts/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import type { Product } from "../types";
import { formatCurrency } from "../utils/format";

export function ProductsPage() {
  const toast = useToast();
  const { user } = useAuth();
  const canManage = user?.permissions.includes("products.manage") ?? false;
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [statusFilter, setStatusFilter] = useState("active");
  const [lowStock, setLowStock] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const { data, loading, setData } = useAsync(async () => {
    const [products, categories, suppliers] = await Promise.all([
      catalogService.listProducts({
        search: deferredSearch || undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        status: statusFilter,
        low_stock: lowStock || undefined,
      }),
      catalogService.listCategories(),
      catalogService.listSuppliers(),
    ]);
    return { products, categories, suppliers };
  }, [deferredSearch, categoryId, statusFilter, lowStock]);
  const [editing, setEditing] = useState<Product | null>(null);
  const [open, setOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function refresh() {
    const products = await catalogService.listProducts({
      search: deferredSearch || undefined,
      category_id: categoryId ? Number(categoryId) : undefined,
      status: statusFilter,
      low_stock: lowStock || undefined,
    });
    setData((current) => (current ? { ...current, products } : current));
  }

  async function handleSubmit(payload: Record<string, unknown>) {
    try {
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
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível salvar o produto.", "error");
      throw error;
    }
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
        {canManage && <Button onClick={() => setOpen(true)}>
          <Plus size={16} className="mr-2" />
          Novo produto
        </Button>}
      </div>
      <Card className="grid gap-4 md:grid-cols-4">
        <label className="space-y-2 text-sm md:col-span-2">
          <span className="text-slate-600">Buscar produto</span>
          <input
            className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
            placeholder="Nome, SKU ou código de barras"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <label className="space-y-2 text-sm">
          <span className="text-slate-600">Categoria</span>
          <select className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
            <option value="">Todas</option>
            {data?.categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
        </label>
        <label className="space-y-2 text-sm">
          <span className="text-slate-600">Situação</span>
          <select className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="active">Ativos</option>
            <option value="inactive">Inativos</option>
            <option value="all">Todos</option>
          </select>
        </label>
        <label className="flex items-center gap-3 text-sm text-slate-600 md:col-span-4">
          <input type="checkbox" checked={lowStock} onChange={(event) => setLowStock(event.target.checked)} />
          Mostrar somente estoque baixo
        </label>
      </Card>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-500">Carregando produtos...</p>
        ) : data.products.length === 0 ? (
          <EmptyState title="Nenhum produto cadastrado" description="Cadastre o primeiro item para começar a vender." />
        ) : (
          <DataTable headers={["Nome", "Marca", "SKU", "Categoria", "Custo", "Venda", "Margem", "Estoque", "Status", ...(canManage ? ["Ações"] : [])]}>
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
                {canManage && <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => { setEditing(product); setOpen(true); }}>
                      <Pencil size={16} />
                    </Button>
                    <Button variant="ghost" disabled={deletingId === product.id} onClick={() => handleDelete(product)}>
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </td>}
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
