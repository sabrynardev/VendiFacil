import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { CategoryForm } from "../components/CategoryForm";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import type { Category } from "../types";

export function CategoriesPage() {
  const toast = useToast();
  const { data, loading, setData } = useAsync(() => catalogService.listCategories(), []);
  const [editing, setEditing] = useState<Category | null>(null);
  const [open, setOpen] = useState(false);

  function close() {
    setOpen(false);
    setEditing(null);
  }

  async function save(payload: { name: string; description: string }) {
    try {
      const saved = editing
        ? await catalogService.updateCategory(editing.id, payload)
        : await catalogService.createCategory(payload);
      setData((current) => {
        const categories = editing
          ? (current ?? []).map((item) => item.id === saved.id ? saved : item)
          : [...(current ?? []), saved];
        return categories.sort((a, b) => a.name.localeCompare(b.name));
      });
      toast.push(editing ? "Categoria atualizada com sucesso." : "Categoria criada com sucesso.");
      close();
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível salvar a categoria.", "error");
      throw error;
    }
  }

  async function remove(category: Category) {
    if (!window.confirm(`Excluir a categoria "${category.name}"?`)) return;
    try {
      await catalogService.deleteCategory(category.id);
      setData((current) => (current ?? []).filter((item) => item.id !== category.id));
      toast.push("Categoria excluída com sucesso.");
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível excluir a categoria.", "error");
    }
  }

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
      <div>
        <h1 className="page-title">Categorias</h1>
        <p className="page-subtitle">Organize os produtos para facilitar buscas, estoque e relatórios.</p>
      </div>
      <Button onClick={() => setOpen(true)}><Plus size={16} className="mr-2" />Nova categoria</Button>
    </div>
    <Card>
      {loading || !data ? <p className="text-sm text-slate-500">Carregando categorias...</p> : data.length === 0 ?
        <EmptyState title="Nenhuma categoria" description="Crie a primeira categoria para organizar seus produtos." /> :
        <DataTable headers={["Nome", "Descrição", "Criada em", "Ações"]}>
          {data.map((category) => <tr key={category.id}>
            <td className="px-4 py-3 font-medium">{category.name}</td>
            <td className="px-4 py-3 text-slate-600">{category.description || "Sem descrição"}</td>
            <td className="px-4 py-3">{new Date(category.created_at).toLocaleDateString("pt-BR")}</td>
            <td className="px-4 py-3"><div className="flex gap-2">
              <Button variant="ghost" onClick={() => { setEditing(category); setOpen(true); }}><Pencil size={16} /></Button>
              <Button variant="ghost" onClick={() => remove(category)}><Trash2 size={16} /></Button>
            </div></td>
          </tr>)}
        </DataTable>}
    </Card>
    {open && <Modal title={editing ? "Editar categoria" : "Nova categoria"} onClose={close}>
      <CategoryForm initialValue={editing} onCancel={close} onSubmit={save} />
    </Modal>}
  </div>;
}
