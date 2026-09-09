import { Badge } from "../components/Badge";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { Skeleton } from "../components/Skeleton";
import { StatCard } from "../components/StatCard";
import { PeriodFilter, periodDates } from "../components/PeriodFilter";
import { useAuth } from "../contexts/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { analyticsService } from "../services/analytics";
import { intelligenceService } from "../services/intelligence";
import { dashboardService } from "../services/dashboard";
import { formatCurrency } from "../utils/format";
import { useState } from "react";
import { Link } from "react-router-dom";

function DashboardInsights({ start, end }: { start: string; end: string }) {
  const { data } = useAsync(() => intelligenceService.insights(start, end), [start, end]);
  if (!data?.insights.length) return null;
  return <Card><div className="flex items-center justify-between"><div><p className="text-xs uppercase tracking-[0.25em] text-brand">Atenção hoje</p><h2 className="mt-2 text-lg font-semibold">Prioridades do Vendi Inteligente</h2></div><Link className="text-sm font-medium text-brand" to="/intelligence">Ver todos</Link></div><div className="mt-4 grid gap-3 lg:grid-cols-3">{data.insights.slice(0, 3).map(item => <div key={item.id} className="rounded-2xl border border-stroke bg-brand/4 p-4"><Badge label={item.priority}/><p className="mt-3 font-medium">{item.title}</p><p className="mt-2 text-sm leading-5 text-slate-600">{item.message}</p></div>)}</div></Card>;
}

const paymentColors = ["#011C6B", "#01258F", "#0231BD", "#023BE6"];

function AnalyticsDashboard() {
  const initial = periodDates("7d"); const [start,setStart]=useState(initial[0]); const [end,setEnd]=useState(initial[1]);
  const {data,loading}=useAsync(()=>analyticsService.overview(start,end),[start,end]);
  if(loading||!data)return <div className="space-y-6"><Skeleton className="h-28 w-full"/><Skeleton className="h-80"/></div>;
  const max=Math.max(...data.sales.timeline.map(item=>item.revenue),1);
  return <div className="space-y-6"><Card className="overflow-hidden p-0"><div className="grid gap-6 bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(1,37,143,0.10),_transparent_28%),linear-gradient(180deg,#ffffff_0%,#eef4ff_100%)] px-6 py-7 md:grid-cols-[1.4fr_0.6fr] md:px-8"><div><p className="text-xs uppercase tracking-[0.35em] text-brand">Painel analítico</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-brandDeeper md:text-4xl">Decisões claras para o seu mercadinho.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">Compare desempenho, margem, estoque e fiado usando os dados reais do período.</p></div><PeriodFilter start={start} end={end} onChange={(from,to)=>{setStart(from);setEnd(to);}}/></div></Card>
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{[["Faturamento",data.summary.revenue],["Lucro bruto",data.summary.gross_profit],["Resultado estimado",data.summary.estimated_result],["Fiado pendente",data.credit.open_total]].map(([label,value])=><Card key={String(label)}><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-semibold">{formatCurrency(Number(value))}</p></Card>)}</div>
  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><Card><p className="text-sm text-slate-500">Vendas</p><p className="mt-2 text-3xl font-semibold">{data.summary.sales_count}</p></Card><Card><p className="text-sm text-slate-500">Ticket médio</p><p className="mt-2 text-3xl font-semibold">{formatCurrency(data.summary.average_ticket)}</p></Card><Card><p className="text-sm text-slate-500">CMV</p><p className="mt-2 text-3xl font-semibold">{formatCurrency(data.summary.cmv)}</p></Card><Card><p className="text-sm text-slate-500">Margem bruta</p><p className="mt-2 text-3xl font-semibold">{data.summary.gross_margin.toFixed(2)}%</p></Card></div>
  <div className="grid gap-6 xl:grid-cols-3"><Card className="xl:col-span-2"><h2 className="text-lg font-semibold">Evolução do faturamento</h2>{data.sales.timeline.every(item=>!item.revenue)?<EmptyState title="Sem vendas no período" description="Escolha outro período ou registre novas vendas."/>:<div className="mt-5 flex h-64 items-end gap-2 overflow-x-auto">{data.sales.timeline.map(item=><div key={item.date} className="flex h-full min-w-10 flex-1 flex-col justify-end" title={`${item.date}: ${formatCurrency(item.revenue)}`}><div className="rounded-t-xl bg-[linear-gradient(180deg,#023BE6_0%,#011C6B_100%)]" style={{height:`${Math.max(item.revenue/max*100,3)}%`}}/><p className="mt-2 text-center text-[10px] text-slate-500">{item.date.slice(8)}</p></div>)}</div>}</Card><Card><h2 className="text-lg font-semibold">Produtos de maior impacto</h2>{!data.products.top_profit.length?<EmptyState title="Sem dados" description="O ranking aparecerá após as vendas."/>:<div className="mt-4 space-y-3">{data.products.top_profit.slice(0,5).map((item,index)=><div key={item.product_id} className="flex justify-between rounded-2xl bg-brand/5 p-3 text-sm"><span>{index+1}. {item.product}</span><strong>{formatCurrency(item.profit)}</strong></div>)}</div>}</Card></div>
  <div className="grid gap-6 lg:grid-cols-3"><Card><p className="text-sm text-slate-500">Estoque a custo</p><p className="mt-2 text-2xl font-semibold">{formatCurrency(data.products.inventory.cost_value)}</p></Card><Card><p className="text-sm text-slate-500">Produtos parados</p><p className="mt-2 text-2xl font-semibold">{data.products.stopped.length}</p></Card><Card><p className="text-sm text-slate-500">Fiado vencido</p><p className="mt-2 text-2xl font-semibold text-rose-600">{formatCurrency(data.credit.overdue_total)}</p></Card></div><DashboardInsights start={start} end={end}/></div>;
}

function OperationalDashboard() {
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

  const totalRevenue = data.revenue.reduce((sum, point) => sum + point.revenue, 0);
  const maxRevenue = Math.max(...data.revenue.map((point) => point.revenue), 1);
  const totalPayments = data.paymentMethods.reduce((sum, item) => sum + item.total, 0);
  const maxCategorySales = Math.max(...data.categorySales.map((item) => item.sales), 1);

  return (
    <div className="space-y-6">
      <Card className="overflow-hidden p-0">
        <div className="grid gap-6 bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(1,37,143,0.10),_transparent_28%),linear-gradient(180deg,#ffffff_0%,#eef4ff_100%)] px-6 py-7 md:grid-cols-[1.4fr_0.6fr] md:px-8">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-brand">Painel Operacional</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-brandDeeper md:text-4xl">Resumo do mercadinho em tempo real.</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
              Acompanhe receita, ritmo de vendas, mix por categoria e alertas de ruptura em uma visão pronta para operação diária e apresentação.
            </p>
          </div>
          <div className="grid gap-3 self-start sm:grid-cols-3 md:grid-cols-1">
            <div className="rounded-2xl border border-stroke bg-white/80 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Últimos 7 dias</p>
              <p className="mt-2 text-xl font-semibold text-brandDeeper">{formatCurrency(totalRevenue)}</p>
            </div>
            <div className="rounded-2xl border border-stroke bg-white/80 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Top categoria</p>
              <p className="mt-2 text-xl font-semibold text-brandDeeper">{data.categorySales[0]?.category ?? "Sem dados"}</p>
            </div>
            <div className="rounded-2xl border border-stroke bg-white/80 px-4 py-3">
              <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Alerta imediato</p>
              <p className="mt-2 text-xl font-semibold text-brandDeeper">{data.alerts.length} item(ns)</p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid gap-4 xl:grid-cols-4">
        <StatCard title="Faturamento hoje" value={data.summary.revenue_today.value} delta={data.summary.revenue_today.delta} currency />
        <StatCard title="Vendas hoje" value={data.summary.sales_today.value} delta={data.summary.sales_today.delta} />
        <StatCard title="Ticket médio" value={data.summary.average_ticket.value} delta={data.summary.average_ticket.delta} currency />
        <Card>
          <p className="text-sm text-slate-500">Produtos com estoque baixo</p>
          <p className="mt-2 text-3xl font-semibold text-brandDeeper">{data.summary.low_stock_products}</p>
          <p className="mt-4 text-sm text-brandStrong">Acompanhe os alertas antes de romper estoque.</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Faturamento nos últimos 7 dias</h2>
            <p className="text-sm text-slate-500">Pico: {formatCurrency(maxRevenue)}</p>
          </div>
          <div className="grid h-72 grid-cols-7 items-end gap-3">
            {data.revenue.map((point) => {
              const height = Math.max((point.revenue / maxRevenue) * 100, point.revenue > 0 ? 16 : 8);
              return (
                <div key={point.day} className="flex h-full flex-col justify-end">
                  <div
                    className="rounded-t-[1rem] bg-[linear-gradient(180deg,#023BE6_0%,#011C6B_100%)] shadow-[0_16px_30px_rgba(2,59,230,0.18)]"
                    style={{ height: `${height}%` }}
                    title={`${point.day}: ${formatCurrency(point.revenue)}`}
                  />
                  <p className="mt-3 text-center text-xs text-slate-500">{point.day}</p>
                  <p className="mt-1 text-center text-xs font-medium text-brandDeeper">{formatCurrency(point.revenue)}</p>
                </div>
              );
            })}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold">Formas de pagamento</h2>
          {data.paymentMethods.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="Sem pagamentos" description="Os métodos aparecerão após as primeiras vendas." />
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {data.paymentMethods.map((entry, index) => {
                const percentage = totalPayments > 0 ? (entry.total / totalPayments) * 100 : 0;
                return (
                  <div key={entry.method} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: paymentColors[index % paymentColors.length] }} />
                        <span className="font-medium text-brandDeeper">{entry.method}</span>
                      </div>
                      <span className="text-slate-500">{formatCurrency(entry.total)}</span>
                    </div>
                    <div className="h-3 rounded-full bg-brand/10">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.max(percentage, entry.total > 0 ? 8 : 0)}%`,
                          background: `linear-gradient(90deg, ${paymentColors[index % paymentColors.length]}, #023BE6)`,
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-500">{percentage.toFixed(1)}% do volume</p>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <h2 className="text-lg font-semibold">Vendas por categoria</h2>
          {data.categorySales.length === 0 ? (
            <div className="mt-4">
              <EmptyState title="Sem categorias com vendas" description="As barras aparecerão conforme as vendas forem registradas." />
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {data.categorySales.map((item, index) => {
                const width = (item.sales / maxCategorySales) * 100;
                return (
                  <div key={item.category} className="rounded-2xl border border-stroke/70 bg-white/80 p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-[0.22em] text-slate-500">#{index + 1}</p>
                        <p className="mt-1 font-semibold text-brandDeeper">{item.category}</p>
                      </div>
                      <p className="text-sm font-medium text-brandStrong">{item.sales} venda(s)</p>
                    </div>
                    <div className="mt-3 h-3 rounded-full bg-brand/10">
                      <div
                        className="h-full rounded-full bg-[linear-gradient(90deg,#011C6B_0%,#0231BD_100%)]"
                        style={{ width: `${Math.max(width, item.sales > 0 ? 10 : 0)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>

        <Card>
          <h2 className="text-lg font-semibold">Mais vendidos</h2>
          <div className="mt-4 space-y-3">
            {data.topProducts.length === 0 ? (
              <EmptyState title="Sem dados de vendas" description="O ranking aparecerá assim que houver vendas registradas." />
            ) : (
              data.topProducts.map((item, index) => (
                <div key={item.product} className="flex items-center justify-between rounded-2xl border border-stroke/70 bg-brand/4 px-4 py-3">
                  <div>
                    <p className="text-sm text-slate-500">{index + 1}.</p>
                    <p className="font-medium">{item.product}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-brandStrong">{item.quantity} un.</span>
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
              <div key={alert.product_id} className="rounded-2xl border border-stroke/70 bg-brand/4 p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold">{alert.product_name}</p>
                    <p className="mt-2 text-sm text-slate-600">{alert.stock_quantity} unidades restantes</p>
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

export function DashboardPage() {
  const { user } = useAuth();
  return user?.permissions.includes("analytics.view") ? <AnalyticsDashboard/> : <OperationalDashboard/>;
}
