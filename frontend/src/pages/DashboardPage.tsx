import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { Skeleton } from "../components/Skeleton";
import { StatCard } from "../components/StatCard";
import { useAsync } from "../hooks/useAsync";
import { dashboardService } from "../services/dashboard";
import { Badge } from "../components/Badge";
import { formatCurrency } from "../utils/format";

const paymentColors = ["#10B981", "#3B82F6", "#F59E0B", "#8B5CF6"];

export function DashboardPage() {
  const { data, loading } = useAsync(async () => {
    const [summary, revenue, topProducts, paymentMethods, categorySales, alerts] = await Promise.all([
      dashboardService.getSummary(),
      dashboardService.getRevenue(),
      dashboardService.getTopProducts(),
      dashboardService.getPaymentMethods(),
      dashboardService.getCategorySales(),
      dashboardService.getAlerts(),
    ]);
    return { summary, revenue, topProducts, paymentMethods, categorySales, alerts };
  }, []);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-80" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="grid gap-6 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.22),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.16),_transparent_28%),linear-gradient(135deg,#0f172a_0%,#111827_55%,#0b1220_100%)] px-6 py-7 md:grid-cols-[1.4fr_0.6fr] md:px-8">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-brand">Painel Operacional</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white md:text-4xl">Resumo do mercadinho em tempo real.</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">
              Acompanhe receita, ritmo de vendas, mix por categoria e alertas de ruptura em uma visão pronta para operação diária e apresentação.
            </p>
          </div>
          <div className="grid gap-3 self-start sm:grid-cols-3 md:grid-cols-1">
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Últimos 7 dias</p>
              <p className="mt-2 text-xl font-semibold text-white">{formatCurrency(data.revenue.reduce((sum, point) => sum + point.revenue, 0))}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Top categoria</p>
              <p className="mt-2 text-xl font-semibold text-white">{data.categorySales[0]?.category ?? "Sem dados"}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Alerta imediato</p>
              <p className="mt-2 text-xl font-semibold text-white">{data.alerts.length} item(ns)</p>
            </div>
          </div>
        </div>
      </Card>
      <div className="grid gap-4 xl:grid-cols-4">
        <StatCard title="Faturamento hoje" value={data.summary.revenue_today.value} delta={data.summary.revenue_today.delta} currency />
        <StatCard title="Vendas hoje" value={data.summary.sales_today.value} delta={data.summary.sales_today.delta} />
        <StatCard title="Ticket médio" value={data.summary.average_ticket.value} delta={data.summary.average_ticket.delta} currency />
        <Card>
          <p className="text-sm text-slate-400">Produtos com estoque baixo</p>
          <p className="mt-2 text-3xl font-semibold">{data.summary.low_stock_products}</p>
          <p className="mt-4 text-sm text-amber-300">Acompanhe os alertas antes de romper estoque.</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <div className="mb-5">
            <h2 className="text-lg font-semibold">Faturamento nos últimos 7 dias</h2>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.revenue}>
                <CartesianGrid stroke="#243047" strokeDasharray="3 3" />
                <XAxis dataKey="day" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Line dataKey="revenue" stroke="#10B981" strokeWidth={3} dot={{ fill: "#10B981" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="text-lg font-semibold">Formas de pagamento</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data.paymentMethods} dataKey="total" nameKey="method" innerRadius={60} outerRadius={95}>
                  {data.paymentMethods.map((entry, index) => (
                    <Cell key={entry.method} fill={paymentColors[index % paymentColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {data.paymentMethods.map((entry, index) => (
              <div key={entry.method} className="flex items-center gap-2 rounded-full bg-slate-900/70 px-3 py-1.5 text-xs text-slate-300">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: paymentColors[index % paymentColors.length] }} />
                {entry.method}
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <h2 className="text-lg font-semibold">Vendas por categoria</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.categorySales}>
                <CartesianGrid stroke="#243047" strokeDasharray="3 3" />
                <XAxis dataKey="category" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Bar dataKey="sales" fill="#3B82F6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="text-lg font-semibold">Mais vendidos</h2>
          <div className="mt-4 space-y-3">
            {data.topProducts.length === 0 ? (
              <EmptyState title="Sem dados de vendas" description="O ranking aparecerá assim que houver vendas registradas." />
            ) : (
              data.topProducts.map((item, index) => (
                <div key={item.product} className="flex items-center justify-between rounded-2xl border border-stroke/70 bg-slate-900/70 px-4 py-3">
                  <div>
                    <p className="text-sm text-slate-400">{index + 1}.</p>
                    <p className="font-medium">{item.product}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-emerald-300">{item.quantity} un.</span>
                    <p className="mt-1 text-xs text-slate-500">maior giro</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="text-lg font-semibold">Alertas de estoque</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {data.alerts.length === 0 ? (
            <div className="md:col-span-3">
              <EmptyState title="Tudo em ordem" description="Nenhum produto está abaixo do nível configurado no momento." />
            </div>
          ) : (
            data.alerts.map((alert) => (
              <div key={alert.product_id} className="rounded-2xl border border-stroke/70 bg-slate-900/70 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{alert.product_name}</p>
                    <p className="mt-2 text-sm text-slate-400">{alert.stock_quantity} unidades restantes</p>
                    <p className="text-sm text-slate-500">Mínimo: {alert.minimum_stock}</p>
                  </div>
                  <Badge label={alert.status} />
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}
