import { useState } from "react";
import { Card } from "../components/Card";
import { useAsync } from "../hooks/useAsync";
import { reportsService } from "../services/reports";
import { formatCurrency } from "../utils/format";

const periods = [
  { value: "today", label: "Hoje" },
  { value: "7d", label: "7 dias" },
  { value: "30d", label: "30 dias" },
];

export function ReportsPage() {
  const [period, setPeriod] = useState("7d");
  const { data, loading } = useAsync(() => reportsService.summary(period), [period]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="page-title">Relatórios</h1>
          <p className="page-subtitle">Resumo consolidado por período com indicadores de faturamento e margem estimada.</p>
        </div>
        <select
          className="rounded-xl border border-stroke bg-white px-4 py-2 text-sm text-brandDeeper"
          value={period}
          onChange={(event) => setPeriod(event.target.value)}
        >
          {periods.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>
      {loading || !data ? (
        <Card>
          <p className="text-sm text-slate-500">Gerando relatório...</p>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Card>
            <p className="text-sm text-slate-500">Faturamento</p>
            <p className="mt-2 text-3xl font-semibold text-brandDeeper">{formatCurrency(data.revenue)}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Vendas</p>
            <p className="mt-2 text-3xl font-semibold text-brandDeeper">{data.sales_count}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Ticket médio</p>
            <p className="mt-2 text-3xl font-semibold text-brandDeeper">{formatCurrency(data.average_ticket)}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Lucro estimado</p>
            <p className="mt-2 text-3xl font-semibold text-brandStrong">{formatCurrency(data.estimated_profit)}</p>
          </Card>
          <Card>
            <p className="text-sm text-slate-500">Itens vendidos</p>
            <p className="mt-2 text-3xl font-semibold text-brandDeeper">{data.items_sold}</p>
          </Card>
        </div>
      )}
    </div>
  );
}
