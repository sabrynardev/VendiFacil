import { Link2, Pencil, Plus, Trash2 } from "lucide-react";
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
import { purchaseService } from "../services/management";
import type { ProductSupplier, Supplier } from "../types";

export function SuppliersPage() {
  const toast = useToast();
  const { data, loading, setData } = useAsync(() => catalogService.listSuppliers(), []);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [open, setOpen] = useState(false);
  const { data: products } = useAsync(() => catalogService.listProducts(), []);
  const [linking, setLinking] = useState<Supplier | null>(null);
  const [links, setLinks] = useState<ProductSupplier[]>([]);
  const [linkForm, setLinkForm] = useState({ product_id: 0, supplier_code: "", preferred: false, lead_time_days: 0 });

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

  async function openLinks(supplier: Supplier) {
    setLinking(supplier);
    setLinks(await purchaseService.supplierProducts(supplier.id));
  }

  async function addLink() {
    if (!linking || !linkForm.product_id) return;
    try {
      await purchaseService.linkProduct(linking.id, linkForm);
      setLinks(await purchaseService.supplierProducts(linking.id));
      setLinkForm({ product_id: 0, supplier_code: "", preferred: false, lead_time_days: 0 });
      toast.push("Produto vinculado ao fornecedor.");
      await refresh();
    } catch (error) {
      toast.push(error instanceof Error ? error.message : "Não foi possível vincular o produto.", "error");
    }
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
                    <Button variant="ghost" onClick={() => void openLinks(supplier)}><Link2 size={16} /></Button>
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
      {linking && <Modal title={`Produtos · ${linking.name}`} onClose={() => setLinking(null)}><div className="space-y-4"><Card className="grid gap-2 bg-brand/4 md:grid-cols-2"><select className="rounded-xl border-stroke bg-white" value={linkForm.product_id} onChange={(event)=>setLinkForm({...linkForm,product_id:Number(event.target.value)})}><option value={0}>Selecione um produto</option>{products?.map(product=><option key={product.id} value={product.id}>{product.name}</option>)}</select><input placeholder="Código no fornecedor" className="rounded-xl border-stroke bg-white" value={linkForm.supplier_code} onChange={(event)=>setLinkForm({...linkForm,supplier_code:event.target.value})}/><label className="text-sm">Prazo médio em dias<input type="number" min="0" className="mt-1 w-full rounded-xl border-stroke bg-white" value={linkForm.lead_time_days} onChange={(event)=>setLinkForm({...linkForm,lead_time_days:Number(event.target.value)})}/></label><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={linkForm.preferred} onChange={(event)=>setLinkForm({...linkForm,preferred:event.target.checked})}/>Fornecedor principal</label><Button className="md:col-span-2" disabled={!linkForm.product_id} onClick={()=>void addLink()}>Vincular produto</Button></Card>{!links.length?<EmptyState title="Nenhum produto vinculado" description="Adicione produtos fornecidos por esta empresa."/>:links.map(link=><div key={link.id} className="flex justify-between rounded-xl border border-stroke p-3 text-sm"><span><b>{link.product_name}</b>{link.supplier_code?` · ${link.supplier_code}`:""}</span><span>{link.preferred?"Principal":"Alternativo"}{link.last_price!=null?` · R$ ${link.last_price.toFixed(2)}`:""}</span></div>)}</div></Modal>}
    </div>
  );
}
