import { History, PackageCheck, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useAuth } from "../contexts/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import { purchaseService } from "../services/management";
import type { PriceHistory, Product, PurchaseOrder, Supplier } from "../types";
import { formatCurrency, formatDateTime } from "../utils/format";

type OrderLine = { product_id: number; quantity: number; unit_cost: number };
type ReceiptLine = { order_item_id: number; quantity: number; unit_cost: number; lot_code: string; expiration_date: string };

export function PurchasesPage() {
  const toast = useToast();
  const { user } = useAuth();
  const canManage = user?.permissions.includes("purchases.manage") ?? false;
  const { data, loading, setData } = useAsync(() => purchaseService.list(), []);
  const { data: catalog } = useAsync(async () => ({ suppliers: await catalogService.listSuppliers(), products: await catalogService.listProducts() }), []);
  const [createOpen, setCreateOpen] = useState(false);
  const [supplierId, setSupplierId] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [notes, setNotes] = useState("");
  const [lines, setLines] = useState<OrderLine[]>([{ product_id: 0, quantity: 1, unit_cost: 0 }]);
  const [receiving, setReceiving] = useState<PurchaseOrder | null>(null);
  const [receiptLines, setReceiptLines] = useState<ReceiptLine[]>([]);
  const [prices, setPrices] = useState<PriceHistory[] | null>(null);

  async function refresh() { setData(await purchaseService.list()); }
  async function createOrder(event: React.FormEvent) {
    event.preventDefault();
    try {
      await purchaseService.create({ supplier_id: supplierId, discount, notes, items: lines });
      toast.push("Pedido criado com sucesso."); setCreateOpen(false); setLines([{ product_id: 0, quantity: 1, unit_cost: 0 }]); setDiscount(0); setNotes(""); await refresh();
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível criar o pedido.", "error"); }
  }
  function openReceipt(order: PurchaseOrder) {
    setReceiving(order);
    setReceiptLines(order.items.filter((item) => item.pending_quantity > 0).map((item) => ({ order_item_id: item.id, quantity: item.pending_quantity, unit_cost: item.unit_cost, lot_code: "", expiration_date: "" })));
  }
  async function receiveOrder() {
    if (!receiving) return;
    try {
      await purchaseService.receive(receiving.id, { items: receiptLines.filter((line) => line.quantity > 0).map((line) => ({ ...line, expiration_date: line.expiration_date || null, lot_code: line.lot_code || null })) });
      toast.push("Recebimento registrado e estoque atualizado."); setReceiving(null); await refresh();
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível receber o pedido.", "error"); }
  }
  const subtotal = lines.reduce((sum, line) => sum + line.quantity * line.unit_cost, 0);
  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center"><div><h1 className="page-title">Compras</h1><p className="page-subtitle">Pedidos, recebimentos parciais e histórico de custos.</p></div><div className="flex gap-2"><Button variant="secondary" onClick={async()=>setPrices(await purchaseService.priceHistory())}><History size={16} className="mr-2"/>Histórico de preços</Button>{canManage && <Button onClick={()=>setCreateOpen(true)}><Plus size={16} className="mr-2"/>Novo pedido</Button>}</div></div>
    <Card>{loading||!data?<p className="text-sm text-slate-500">Carregando pedidos...</p>:!data.length?<EmptyState title="Nenhum pedido" description="Crie um pedido para iniciar o abastecimento."/>:<DataTable headers={["Pedido","Fornecedor","Data","Itens","Recebido","Total","Status","Ações"]}>{data.map(order=><tr key={order.id}><td className="px-4 py-3 font-medium">{order.number}</td><td className="px-4 py-3">{order.supplier_name}</td><td className="px-4 py-3">{new Date(order.order_date+"T12:00:00").toLocaleDateString("pt-BR")}</td><td className="px-4 py-3">{order.items.length}</td><td className="px-4 py-3">{order.items.reduce((s,i)=>s+i.received_quantity,0)} / {order.items.reduce((s,i)=>s+i.ordered_quantity,0)}</td><td className="px-4 py-3">{formatCurrency(order.total)}</td><td className="px-4 py-3"><Badge label={order.status}/></td><td className="px-4 py-3"><div className="flex gap-2">{!["RECEBIDO","CANCELADO"].includes(order.status)&&<Button variant="secondary" onClick={()=>openReceipt(order)}><PackageCheck size={15} className="mr-1"/>Receber</Button>}{!["RECEBIDO","PARCIALMENTE_RECEBIDO","CANCELADO"].includes(order.status)&&<Button variant="ghost" onClick={async()=>{await purchaseService.cancel(order.id);toast.push("Pedido cancelado.");await refresh();}}><Trash2 size={15}/></Button>}</div></td></tr>)}</DataTable>}</Card>
    {createOpen&&<Modal title="Novo pedido de compra" onClose={()=>setCreateOpen(false)}><form className="space-y-4" onSubmit={createOrder}><label className="block text-sm">Fornecedor<select required className="mt-1 w-full rounded-xl border-stroke bg-white" value={supplierId} onChange={e=>setSupplierId(Number(e.target.value))}><option value={0}>Selecione</option>{catalog?.suppliers.map((item:Supplier)=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label><div className="space-y-3">{lines.map((line,index)=><Card key={index} className="grid gap-2 bg-brand/4 md:grid-cols-[2fr_1fr_1fr_auto]"><select required className="rounded-xl border-stroke bg-white" value={line.product_id} onChange={e=>setLines(current=>current.map((item,i)=>i===index?{...item,product_id:Number(e.target.value)}:item))}><option value={0}>Produto</option>{catalog?.products.map((item:Product)=><option key={item.id} value={item.id}>{item.name}</option>)}</select><input aria-label="Quantidade" type="number" min="0.001" step="0.001" className="rounded-xl border-stroke bg-white" value={line.quantity} onChange={e=>setLines(current=>current.map((item,i)=>i===index?{...item,quantity:Number(e.target.value)}:item))}/><input aria-label="Custo unitário" type="number" min="0" step="0.01" className="rounded-xl border-stroke bg-white" value={line.unit_cost} onChange={e=>setLines(current=>current.map((item,i)=>i===index?{...item,unit_cost:Number(e.target.value)}:item))}/><Button type="button" variant="ghost" onClick={()=>setLines(current=>current.filter((_,i)=>i!==index))}><Trash2 size={15}/></Button></Card>)}</div><Button type="button" variant="secondary" onClick={()=>setLines(current=>[...current,{product_id:0,quantity:1,unit_cost:0}])}>Adicionar item</Button><div className="grid gap-3 md:grid-cols-2"><label className="text-sm">Desconto<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={discount} onChange={e=>setDiscount(Number(e.target.value))}/></label><label className="text-sm">Observações<input className="mt-1 w-full rounded-xl border-stroke bg-white" value={notes} onChange={e=>setNotes(e.target.value)}/></label></div><p className="text-right text-xl font-semibold">Total: {formatCurrency(Math.max(subtotal-discount,0))}</p><Button className="w-full" disabled={!supplierId||lines.some(line=>!line.product_id)}>Criar pedido</Button></form></Modal>}
    {receiving&&<Modal title={`Receber pedido ${receiving.number}`} onClose={()=>setReceiving(null)}><div className="space-y-4">{receiptLines.map((line,index)=>{const item=receiving.items.find(candidate=>candidate.id===line.order_item_id)!;return <Card key={line.order_item_id} className="bg-brand/4"><p className="font-medium">{item.product_name}</p><p className="mb-3 text-xs text-slate-500">Solicitado {item.ordered_quantity} · Recebido {item.received_quantity} · Pendente {item.pending_quantity}</p><div className="grid gap-2 md:grid-cols-2"><label className="text-sm">Recebendo agora<input type="number" min="0" max={item.pending_quantity} step="0.001" className="mt-1 w-full rounded-xl border-stroke bg-white" value={line.quantity} onChange={e=>setReceiptLines(current=>current.map((entry,i)=>i===index?{...entry,quantity:Number(e.target.value)}:entry))}/></label><label className="text-sm">Custo efetivo<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={line.unit_cost} onChange={e=>setReceiptLines(current=>current.map((entry,i)=>i===index?{...entry,unit_cost:Number(e.target.value)}:entry))}/></label><label className="text-sm">Lote opcional<input className="mt-1 w-full rounded-xl border-stroke bg-white" value={line.lot_code} onChange={e=>setReceiptLines(current=>current.map((entry,i)=>i===index?{...entry,lot_code:e.target.value}:entry))}/></label><label className="text-sm">Validade opcional<input type="date" className="mt-1 w-full rounded-xl border-stroke bg-white" value={line.expiration_date} onChange={e=>setReceiptLines(current=>current.map((entry,i)=>i===index?{...entry,expiration_date:e.target.value}:entry))}/></label></div></Card>})}<Button className="w-full" onClick={()=>void receiveOrder()}>Confirmar recebimento</Button></div></Modal>}
    {prices&&<Modal title="Histórico de preços" onClose={()=>setPrices(null)}><div className="space-y-2">{!prices.length?<EmptyState title="Sem histórico" description="Os custos aparecerão após os recebimentos."/>:prices.map(item=><div key={item.id} className="grid gap-2 rounded-xl border border-stroke p-3 text-sm md:grid-cols-4"><span>{item.product_name}</span><span>{item.supplier_name}</span><span>{formatCurrency(item.unit_cost)}</span><span className={item.variation_percent&&item.variation_percent>0?"text-rose-600":"text-emerald-600"}>{item.variation_percent==null?"Primeiro preço":`${item.variation_percent>0?"+":""}${item.variation_percent}%`} · {formatDateTime(item.recorded_at)}</span></div>)}</div></Modal>}
  </div>;
}
