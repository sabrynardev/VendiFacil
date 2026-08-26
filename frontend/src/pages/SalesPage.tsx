import { useState } from "react";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useAsync } from "../hooks/useAsync";
import { salesService } from "../services/sales";
import type { Sale } from "../types";
import { formatCurrency, formatDateTime } from "../utils/format";

export function SalesPage() {
  const { data, loading } = useAsync(() => salesService.list(), []);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Vendas</h1>
        <p className="page-subtitle">Histórico de transações com detalhes de itens, operador e pagamento.</p>
      </div>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-400">Carregando vendas...</p>
        ) : data.length === 0 ? (
          <EmptyState title="Nenhuma venda registrada" description="Finalize vendas no caixa para preencher o histórico." />
        ) : (
          <DataTable headers={["Número", "Data", "Operador", "Itens", "Pagamento", "Total"]}>
            {data.map((sale) => (
              <tr key={sale.id} className="cursor-pointer hover:bg-slate-900/80" onClick={() => setSelectedSale(sale)}>
                <td className="px-4 py-3 font-medium">#{String(sale.id).padStart(6, "0")}</td>
                <td className="px-4 py-3">{formatDateTime(sale.created_at)}</td>
                <td className="px-4 py-3">{sale.operator_name}</td>
                <td className="px-4 py-3">{sale.items.length}</td>
                <td className="px-4 py-3">{sale.payment_method}</td>
                <td className="px-4 py-3 text-emerald-300">{formatCurrency(sale.total)}</td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>

      {selectedSale && (
        <Modal title={`Venda #${String(selectedSale.id).padStart(6, "0")}`} onClose={() => setSelectedSale(null)}>
          <div className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Card className="bg-slate-900/70">
                <p className="text-sm text-slate-400">Data</p>
                <p className="mt-2 font-medium">{formatDateTime(selectedSale.created_at)}</p>
              </Card>
              <Card className="bg-slate-900/70">
                <p className="text-sm text-slate-400">Operador</p>
                <p className="mt-2 font-medium">{selectedSale.operator_name}</p>
              </Card>
            </div>
            <div className="space-y-3">
              {selectedSale.items.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-2xl bg-slate-900/70 px-4 py-3">
                  <div>
                    <p className="font-medium">{item.product_name}</p>
                    <p className="text-sm text-slate-400">{item.quantity} x {formatCurrency(item.unit_price)}</p>
                  </div>
                  <p className="font-semibold text-emerald-300">{formatCurrency(item.subtotal)}</p>
                </div>
              ))}
            </div>
            <Card className="bg-slate-900/70">
              <div className="flex justify-between text-sm text-slate-400">
                <span>Pagamento</span>
                <span>{selectedSale.payment_method}</span>
              </div>
              <div className="mt-3 flex justify-between text-sm text-slate-400">
                <span>Subtotal</span>
                <span>{formatCurrency(selectedSale.subtotal)}</span>
              </div>
              <div className="mt-3 flex justify-between text-sm text-slate-400">
                <span>Desconto</span>
                <span>{formatCurrency(selectedSale.discount)}</span>
              </div>
              <div className="mt-4 flex justify-between text-xl font-semibold text-slate-50">
                <span>Total</span>
                <span>{formatCurrency(selectedSale.total)}</span>
              </div>
            </Card>
          </div>
        </Modal>
      )}
    </div>
  );
}
