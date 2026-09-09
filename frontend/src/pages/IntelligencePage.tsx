import { Calculator, ExternalLink, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { PeriodFilter, periodDates } from "../components/PeriodFilter";
import { useAsync } from "../hooks/useAsync";
import { intelligenceService } from "../services/intelligence";
import type { VendiInsight } from "../types";
import { formatCurrency, formatDateTime } from "../utils/format";

const categories = ["", "Estoque", "Vendas", "Clientes", "Fornecedores", "Perdas"];
const priorities = ["", "CRITICO", "IMPORTANTE", "ATENCAO", "INFORMATIVO"];

export function IntelligencePage() {
  const initial = periodDates("30d");
  const [start, setStart] = useState(initial[0]);
  const [end, setEnd] = useState(initial[1]);
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [selected, setSelected] = useState<VendiInsight | null>(null);
  const { data, loading, error } = useAsync(() => intelligenceService.insights(start, end, category, priority), [start, end, category, priority]);
  const forecast = data?.forecast.products.filter((item) => item.history_sufficient && (item.coverage_days != null || item.suggested_quantity != null)).sort((a, b) => (a.coverage_days ?? 99999) - (b.coverage_days ?? 99999)) ?? [];

  return <div className="space-y-6">
    <Card className="overflow-hidden p-0"><div className="grid gap-6 bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_34%),linear-gradient(180deg,#ffffff_0%,#eef4ff_100%)] px-6 py-7 md:grid-cols-[1.4fr_0.6fr] md:px-8"><div><p className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-brand"><Sparkles size={16}/> Vendi Inteligente</p><h1 className="mt-3 text-3xl font-semibold tracking-tight text-brandDeeper">Decisões explicadas pelos seus dados.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">Prioridades de estoque, vendas, clientes e fornecedores, calculadas sem inventar informações.</p></div><PeriodFilter start={start} end={end} onChange={(from, to) => { setStart(from); setEnd(to); }}/></div></Card>
    <div className="flex flex-wrap gap-3"><label className="text-sm text-slate-600">Categoria<select className="mt-1 block rounded-xl border-stroke bg-white" value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map(item => <option key={item} value={item}>{item || "Todas"}</option>)}</select></label><label className="text-sm text-slate-600">Prioridade<select className="mt-1 block rounded-xl border-stroke bg-white" value={priority} onChange={(event) => setPriority(event.target.value)}>{priorities.map(item => <option key={item} value={item}>{item ? item.replace("ATENCAO", "ATENÇÃO") : "Todas"}</option>)}</select></label></div>
    {error && <Card><p className="text-sm text-rose-600">{error}</p></Card>}
    {loading ? <Card><p className="text-sm text-slate-500">Calculando recomendações...</p></Card> : data ? <>
      {!data.insights.length ? <Card><EmptyState title="Nenhum insight relevante para estes filtros" description="O Vendi recalcula as recomendações quando vendas, estoque, compras, perdas ou pagamentos mudam."/></Card> : <div className="grid gap-4 lg:grid-cols-2">{data.insights.map(item => <Card key={item.id}><div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.category}</p><h2 className="mt-2 text-lg font-semibold">{item.title}</h2></div><Badge label={item.priority}/></div><p className="mt-3 text-sm leading-6 text-slate-600">{item.message}</p><p className="mt-3 text-xs text-slate-400">Calculado em {formatDateTime(item.calculated_at)}</p><div className="mt-4 flex flex-wrap gap-2"><Button variant="secondary" onClick={() => setSelected(item)}><Calculator size={15} className="mr-2"/>Como foi calculado?</Button>{item.action && <Link to={item.action.path}><Button variant="ghost">{item.action.label}<ExternalLink size={14} className="ml-2"/></Button></Link>}</div></Card>)}</div>}
      <Card><div className="mb-4"><h2 className="font-semibold">Previsão de cobertura e reposição</h2><p className="text-sm text-slate-500">Média dos últimos {data.forecast.period.window_days} dias, incluindo dias sem venda.</p></div>{!forecast.length ? <EmptyState title="Ainda não há histórico suficiente para previsões" description="Cada produto precisa de pelo menos duas vendas na janela analisada."/> : <DataTable headers={["Produto", "Estoque", "Média/dia", "Cobertura", "Prazo", "Ponto de pedido", "Sugestão"]}>{forecast.map(item => <tr key={item.product_id}><td className="px-4 py-3 font-medium">{item.product}</td><td className="px-4 py-3">{item.stock}</td><td className="px-4 py-3">{item.average_daily_sales}</td><td className="px-4 py-3">{item.coverage_days} dias</td><td className="px-4 py-3">{item.lead_time_days == null ? "Não informado" : `${item.lead_time_days} dias`}</td><td className="px-4 py-3">{item.reorder_point ?? "Sem prazo"}</td><td className="px-4 py-3 font-medium">{item.suggested_quantity == null ? "Revisar prazo" : item.suggested_quantity}</td></tr>)}</DataTable>}</Card>
    </> : null}
    {selected && <Modal title={selected.title} onClose={() => setSelected(null)}><p className="text-sm leading-6 text-slate-600">{selected.explanation}</p><div className="mt-5 rounded-2xl border border-stroke bg-brand/4 p-4"><p className="text-xs uppercase tracking-[0.2em] text-slate-500">Dados utilizados</p><div className="mt-3 grid gap-2 sm:grid-cols-2">{Object.entries(selected.data).map(([key, value]) => <p key={key} className="flex justify-between gap-3 text-sm"><span className="text-slate-500">{key.replace(/_/g, " ")}</span><strong>{typeof value === "number" && key.includes("value") ? formatCurrency(value) : value == null ? "Não informado" : String(value)}</strong></p>)}</div></div></Modal>}
  </div>;
}
