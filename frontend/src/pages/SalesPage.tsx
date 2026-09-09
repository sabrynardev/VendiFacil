import { useState } from "react";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useAsync } from "../hooks/useAsync";
import { salesService } from "../services/sales";
import type { Sale } from "../types";
import { formatCurrency, formatDateTime } from "../utils/format";
import { Button } from "../components/Button";
import { Badge } from "../components/Badge";
import { useToast } from "../components/ToastProvider";

export function SalesPage() {
  const toast = useToast();
  const [statusFilter, setStatusFilter] = useState("");
  const [paymentFilter, setPaymentFilter] = useState("");
  const { data, loading, setData } = useAsync(() => salesService.list({ status: statusFilter || undefined, payment_method: paymentFilter || undefined }), [statusFilter, paymentFilter]);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Vendas</h1>
        <p className="page-subtitle">Histórico de transações com detalhes de itens, operador e pagamento.</p>
      </div>
      <Card className="grid gap-3 md:grid-cols-2">
        <label className="text-sm">Status<select className="mt-1 w-full rounded-xl border-stroke bg-white" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">Todos</option><option value="COMPLETED">Concluídas</option><option value="ON_HOLD">Em espera</option><option value="CANCELLED">Canceladas</option></select></label>
        <label className="text-sm">Pagamento<select className="mt-1 w-full rounded-xl border-stroke bg-white" value={paymentFilter} onChange={(event) => setPaymentFilter(event.target.value)}><option value="">Todos</option><option value="DINHEIRO">Dinheiro</option><option value="PIX">PIX</option><option value="DEBITO">Débito</option><option value="CREDITO">Crédito</option></select></label>
      </Card>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-500">Carregando vendas...</p>
        ) : data.length === 0 ? (
          <EmptyState title="Nenhuma venda registrada" description="Finalize vendas no caixa para preencher o histórico." />
        ) : (
          <DataTable headers={["Número", "Data", "Operador", "Itens", "Pagamento", "Total", "Status"]}>
            {data.map((sale) => (
              <tr key={sale.id} className="cursor-pointer transition hover:bg-brand/5" onClick={() => setSelectedSale(sale)}>
                <td className="px-4 py-3 font-medium">#{String(sale.id).padStart(6, "0")}</td>
                <td className="px-4 py-3">{formatDateTime(sale.created_at)}</td>
                <td className="px-4 py-3">{sale.operator_name}</td>
                <td className="px-4 py-3">{sale.items.length}</td>
                <td className="px-4 py-3">{sale.payment_method}</td>
                <td className="px-4 py-3 text-brandStrong">{formatCurrency(sale.total)}</td>
                <td className="px-4 py-3"><Badge label={sale.status} /></td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>

      {selectedSale && (
        <Modal title={`Venda #${String(selectedSale.id).padStart(6, "0")}`} onClose={() => setSelectedSale(null)}>
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-brand/4">
                <p className="text-sm text-slate-500">Data</p>
                <p className="mt-2 font-medium">{formatDateTime(selectedSale.created_at)}</p>
              </Card>
              <Card className="bg-brand/4">
                <p className="text-sm text-slate-500">Operador</p>
                <p className="mt-2 font-medium">{selectedSale.operator_name}</p>
              </Card>
            </div>
            <div className="space-y-3">
              {selectedSale.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-2xl border border-stroke bg-brand/4 px-4 py-3">
                  <div>
                    <p className="font-medium">{item.product_name}</p>
                    <p className="text-sm text-slate-600">{item.quantity} x {formatCurrency(item.unit_price)}</p>
                  </div>
                  <p className="font-semibold text-brandStrong">{formatCurrency(item.subtotal)}</p>
                </div>
              ))}
            </div>
            <Card className="bg-brand/4">
              <div className="flex justify-between text-sm text-slate-600">
                <span>Pagamento</span>
                <span>{selectedSale.payment_method}</span>
              </div>
              <div className="mt-3 flex justify-between text-sm text-slate-600">
                <span>Subtotal</span>
                <span>{formatCurrency(selectedSale.subtotal)}</span>
              </div>
              <div className="mt-3 space-y-2 border-t border-stroke pt-3 text-sm text-slate-600">
                {selectedSale.payments.map((payment, index) => <div key={`${payment.id}-${index}`} className="flex justify-between"><span>{payment.method}</span><span>{formatCurrency(payment.amount)}</span></div>)}
              </div>
              <div className="mt-3 flex justify-between text-sm text-slate-600">
                <span>Desconto</span>
                <span>{formatCurrency(selectedSale.discount)}</span>
              </div>
              <div className="mt-4 flex justify-between text-xl font-semibold text-brandDeeper">
                <span>Total</span>
                <span>{formatCurrency(selectedSale.total)}</span>
              </div>
            </Card>
            {selectedSale.cancellation_reason && <p className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">Motivo do cancelamento: {selectedSale.cancellation_reason}</p>}
            <div className="flex gap-3 print:hidden"><Button variant="secondary" onClick={() => window.print()}>Imprimir comprovante</Button>{selectedSale.status === "COMPLETED" && <Button variant="danger" onClick={async () => { const reason = window.prompt("Motivo do cancelamento:"); if (!reason) return; try { const updated = await salesService.cancel(selectedSale.id, reason); setSelectedSale(updated); setData((current) => current?.map((sale) => sale.id === updated.id ? updated : sale) ?? null); toast.push("Venda cancelada e estoque restaurado."); } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível cancelar.", "error"); } }}>Cancelar venda</Button>}</div>
          </div>
        </Modal>
      )}
    </div>
  );
}
