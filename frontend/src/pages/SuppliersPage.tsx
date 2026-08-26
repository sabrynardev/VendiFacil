import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { SupplierForm } from "../components/SupplierForm";
import { useToast } from "../components/ToastProvider";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import type { Supplier } from "../types";

export function SuppliersPage() {
  const toast = useToast();
  const { data, loading, setData } = useAsync(() => catalogService.listSuppliers(), []);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [open, setOpen] = useState(false);

  async function refresh() {
    setData(await catalogService.listSuppliers());
  }

  async function handleSubmit(payload: Record<string, unknown>) {
    if (editing) {
      await catalogService.updateSupplier(editing.id, payload);
      toast.push("Fornecedor atualizado com sucesso.");
    } else {
      await catalogService.createSupplier(payload);
      toast.push("Fornecedor criado com sucesso.");
    }
    await refresh();
    setOpen(false);
    setEditing(null);
  }

  async function handleDelete(supplier: Supplier) {
    if (!window.confirm(`Excluir o fornecedor "${supplier.name}"?`)) return;
    await catalogService.deleteSupplier(supplier.id);
    toast.push("Fornecedor removido.");
    await refresh();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="page-title">Fornecedores</h1>
          <p className="page-subtitle">Gestão de contatos, relacionamento com produtos e base de compras futuras.</p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} className="mr-2" />
          Novo fornecedor
        </Button>
      </div>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-400">Carregando fornecedores...</p>
        ) : data.length === 0 ? (
          <EmptyState title="Sem fornecedores" description="Cadastre fornecedores para vincular aos produtos." />
        ) : (
          <DataTable headers={["Nome", "Contato", "E-mail", "Produtos", "Criado em", "Ações"]}>
            {data.map((supplier) => (
              <tr key={supplier.id}>
                <td className="px-4 py-3 font-medium">{supplier.name}</td>
                <td className="px-4 py-3">{supplier.whatsapp || supplier.phone || "-"}</td>
                <td className="px-4 py-3">{supplier.email || "-"}</td>
                <td className="px-4 py-3">{supplier.products_count}</td>
                <td className="px-4 py-3">{new Date(supplier.created_at).toLocaleDateString("pt-BR")}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <Button variant="ghost" onClick={() => { setEditing(supplier); setOpen(true); }}>
                      <Pencil size={16} />
                    </Button>
                    <Button variant="ghost" onClick={() => handleDelete(supplier)}>
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>

      {open && (
        <Modal title={editing ? "Editar fornecedor" : "Novo fornecedor"} onClose={() => { setOpen(false); setEditing(null); }}>
          <SupplierForm initialValue={editing} onSubmit={handleSubmit} onCancel={() => { setOpen(false); setEditing(null); }} />
        </Modal>
      )}
    </div>
  );
}
