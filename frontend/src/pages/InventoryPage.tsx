import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { useAsync } from "../hooks/useAsync";
import { inventoryService } from "../services/inventory";

export function InventoryPage() {
  const { data, loading } = useAsync(async () => {
    const [inventory, movements] = await Promise.all([inventoryService.list(), inventoryService.movements()]);
    return { inventory, movements };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Estoque</h1>
        <p className="page-subtitle">Visão de ruptura, previsão de dias restantes e histórico de movimentações.</p>
      </div>
      <Card>
        {loading || !data ? (
          <p className="text-sm text-slate-500">Carregando estoque...</p>
        ) : data.inventory.length === 0 ? (
          <EmptyState title="Sem itens em estoque" description="Cadastre produtos para visualizar as projeções." />
        ) : (
          <DataTable headers={["Produto", "Estoque", "Mínimo", "Venda média/dia", "Previsão", "Reposição", "Status"]}>
            {data.inventory.map((item) => (
              <tr key={item.product_id}>
                <td className="px-4 py-3">
                  <p className="font-medium">{item.product_name}</p>
                  <p className="text-xs text-slate-500">{item.sku}</p>
                </td>
                <td className="px-4 py-3">{item.stock_quantity}</td>
                <td className="px-4 py-3">{item.minimum_stock}</td>
                <td className="px-4 py-3">{item.average_sales_per_day}</td>
                <td className="px-4 py-3">{item.days_remaining ? `${item.days_remaining} dias` : "Sem dados suficientes"}</td>
                <td className="px-4 py-3">{item.purchase_recommendation}</td>
                <td className="px-4 py-3">
                  <Badge label={item.status} />
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>
      <Card>
        <h2 className="text-lg font-semibold">Movimentações recentes</h2>
        <div className="mt-4 space-y-3">
          {data?.movements.slice(0, 8).map((movement) => (
            <div key={movement.id} className="flex flex-col justify-between gap-2 rounded-2xl border border-stroke bg-brand/4 px-4 py-3 md:flex-row md:items-center">
              <div>
                <p className="font-medium">{movement.product_name}</p>
                <p className="text-sm text-slate-600">{movement.type} • {movement.previous_stock} → {movement.new_stock}</p>
              </div>
              <div className="text-right text-sm text-slate-600">
                <p>{movement.user_name || "Sistema"}</p>
                <p>{new Date(movement.created_at).toLocaleString("pt-BR")}</p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
