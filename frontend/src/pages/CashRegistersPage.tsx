import { useState } from "react";
import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useAsync } from "../hooks/useAsync";
import { cashRegisterService } from "../services/cashRegisters";
import type { CashRegister } from "../types";
import { formatCurrency, formatDateTime } from "../utils/format";

export function CashRegistersPage() {
  const { data, loading } = useAsync(() => cashRegisterService.history(), []);
  const [selected, setSelected] = useState<CashRegister | null>(null);
  async function openDetails(id: number) {
    setSelected(await cashRegisterService.get(id));
  }
  return <div className="space-y-6"><div><h1 className="page-title">Histórico de caixas</h1><p className="page-subtitle">Aberturas, vendas, movimentações, fechamento e diferenças.</p></div><Card>{loading||!data?<p className="text-sm text-slate-500">Carregando caixas...</p>:!data.length?<EmptyState title="Nenhum caixa registrado" description="Abra o primeiro caixa pelo PDV."/>:<DataTable headers={["Caixa","Operador","Abertura","Fechamento","Inicial","Vendido","Diferença","Status"]}>{data.map(item=><tr key={item.id} className="cursor-pointer hover:bg-brand/5" onClick={()=>void openDetails(item.id)}><td className="px-4 py-3 font-medium">#{item.id}</td><td className="px-4 py-3">{item.operator_name}</td><td className="px-4 py-3">{formatDateTime(item.opened_at)}</td><td className="px-4 py-3">{item.closed_at?formatDateTime(item.closed_at):"-"}</td><td className="px-4 py-3">{formatCurrency(item.opening_balance)}</td><td className="px-4 py-3">{formatCurrency(item.summary.total_sales)}</td><td className="px-4 py-3">{item.difference==null?"-":formatCurrency(item.difference)}</td><td className="px-4 py-3"><Badge label={item.status}/></td></tr>)}</DataTable>}</Card>{selected&&<Modal title={`Caixa #${selected.id}`} onClose={()=>setSelected(null)}><div className="space-y-4"><div className="grid gap-3 md:grid-cols-2">{Object.entries({"Saldo inicial":selected.summary.opening_balance,"Dinheiro":selected.summary.cash_sales,"PIX":selected.summary.pix_sales,"Débito":selected.summary.debit_sales,"Crédito":selected.summary.credit_sales,"Suprimentos":selected.summary.supplies,"Sangrias":selected.summary.withdrawals,"Esperado":selected.summary.expected_cash}).map(([label,value])=><Card key={label} className="bg-brand/4"><p className="text-sm text-slate-500">{label}</p><p className="mt-1 font-semibold">{formatCurrency(value)}</p></Card>)}</div><div><h3 className="mb-2 font-semibold">Movimentações</h3>{selected.movements.map(movement=><div key={movement.id} className="flex justify-between border-b border-stroke py-2 text-sm"><span>{movement.type} · {movement.reason || "Sem observação"}</span><span>{formatCurrency(movement.amount)}</span></div>)}</div></div></Modal>}</div>;
}
