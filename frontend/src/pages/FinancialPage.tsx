import { Banknote, CalendarClock, CircleDollarSign, Plus, RefreshCw, TrendingDown, TrendingUp, WalletCards, type LucideIcon } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useAsync } from "../hooks/useAsync";
import { catalogService } from "../services/catalog";
import { financialService } from "../services/financial";
import { purchaseService } from "../services/management";
import type { FinancialReceivable, Payable } from "../types";
import { formatCurrency, formatDate, formatDateTime } from "../utils/format";

const isoDate = (date: Date) => date.toISOString().slice(0, 10);
const today = isoDate(new Date());
const monthStart = `${today.slice(0, 7)}-01`;
const fieldClass = "mt-1 w-full rounded-xl border-stroke bg-white";
const emptyPayable = { description: "", category_id: "", supplier_id: "", purchase_order_id: "", amount: "", due_date: today, notes: "" };
const emptyRevenue = { description: "", category_id: "", amount: "", payment_method: "PIX", notes: "" };
const emptyRecurring = { description: "", category_id: "", amount: "", frequency: "MENSAL", next_due_date: today, notes: "" };

type Tab = "resumo" | "pagar" | "receber" | "fluxo" | "recorrentes";

export function FinancialPage() {
  const toast = useToast();
  const [start, setStart] = useState(monthStart);
  const [end, setEnd] = useState(today);
  const [tab, setTab] = useState<Tab>("resumo");
  const [modal, setModal] = useState<"payable" | "revenue" | "recurring" | null>(null);
  const [payableForm, setPayableForm] = useState(emptyPayable);
  const [revenueForm, setRevenueForm] = useState(emptyRevenue);
  const [recurringForm, setRecurringForm] = useState(emptyRecurring);
  const [paying, setPaying] = useState<Payable | null>(null);
  const [receiving, setReceiving] = useState<FinancialReceivable | null>(null);
  const [payment, setPayment] = useState({ amount: "", method: "PIX", use_cash_register: false });

  const report = useAsync(() => Promise.all([
    financialService.summary(start, end), financialService.payables(), financialService.receivables(), financialService.revenues(),
    financialService.cashFlow(start, end), financialService.projections(), financialService.recurring(), financialService.categories(),
    catalogService.listSuppliers(), purchaseService.list(),
  ]), [start, end]);

  const refresh = async () => report.setData(await Promise.all([
    financialService.summary(start, end), financialService.payables(), financialService.receivables(), financialService.revenues(),
    financialService.cashFlow(start, end), financialService.projections(), financialService.recurring(), financialService.categories(),
    catalogService.listSuppliers(), purchaseService.list(),
  ]));

  if (report.error) return <Card><p className="text-sm text-rose-600">{report.error}</p></Card>;
  if (report.loading || !report.data) return <Card><p className="text-sm text-slate-500">Carregando financeiro...</p></Card>;

  const [summary, payables, receivables, revenues, flow, projections, recurring, categories, suppliers, purchases] = report.data;
  const expenseCategories = categories.filter((item) => item.type === "DESPESA");
  const revenueCategories = categories.filter((item) => item.type === "RECEITA");
  const metrics: Array<[string, number, LucideIcon]> = [
    ["Faturamento", summary.revenue, CircleDollarSign],
    ["Recebimentos", summary.cash_in, WalletCards],
    ["Lucro bruto", summary.gross_profit, TrendingUp],
    ["Resultado estimado", summary.estimated_result, summary.estimated_result >= 0 ? TrendingUp : TrendingDown],
  ];

  async function submitPayable(event: FormEvent) {
    event.preventDefault();
    try {
      await financialService.createPayable({ ...payableForm, category_id: Number(payableForm.category_id), supplier_id: payableForm.supplier_id ? Number(payableForm.supplier_id) : null, purchase_order_id: payableForm.purchase_order_id ? Number(payableForm.purchase_order_id) : null, amount: Number(payableForm.amount) });
      setModal(null); setPayableForm(emptyPayable); await refresh(); toast.push("Conta a pagar criada.");
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível criar a conta.", "error"); }
  }

  async function submitRevenue(event: FormEvent) {
    event.preventDefault();
    try {
      await financialService.createRevenue({ ...revenueForm, category_id: Number(revenueForm.category_id), amount: Number(revenueForm.amount), idempotency_key: crypto.randomUUID() });
      setModal(null); setRevenueForm(emptyRevenue); await refresh(); toast.push("Receita registrada.");
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível registrar a receita.", "error"); }
  }

  async function submitRecurring(event: FormEvent) {
    event.preventDefault();
    try {
      await financialService.createRecurring({ ...recurringForm, category_id: Number(recurringForm.category_id), amount: Number(recurringForm.amount) });
      setModal(null); setRecurringForm(emptyRecurring); await refresh(); toast.push("Despesa recorrente criada.");
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível criar a recorrência.", "error"); }
  }

  async function submitPayment(event: FormEvent) {
    event.preventDefault();
    try {
      const payload = { amount: Number(payment.amount), method: payment.method, use_cash_register: payment.use_cash_register, idempotency_key: crypto.randomUUID() };
      if (paying) await financialService.pay(paying.id, payload);
      if (receiving) await financialService.receive(receiving.source_id, payload);
      setPaying(null); setReceiving(null); await refresh(); toast.push(paying ? "Pagamento registrado." : "Recebimento registrado.");
    } catch (error) { toast.push(error instanceof Error ? error.message : "Não foi possível registrar.", "error"); }
  }

  const tabs: Array<[Tab, string]> = [["resumo", "Resumo"], ["pagar", "Contas a pagar"], ["receber", "Contas a receber"], ["fluxo", "Fluxo de caixa"], ["recorrentes", "Recorrentes"]];

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center"><div><h1 className="page-title">Financeiro</h1><p className="page-subtitle">Faturamento, recebimentos, compromissos e resultado gerencial.</p></div><div className="flex flex-wrap gap-2"><Button variant="secondary" onClick={() => setModal("revenue")}><TrendingUp size={16} className="mr-2"/>Nova receita</Button><Button onClick={() => setModal("payable")}><Plus size={16} className="mr-2"/>Nova despesa</Button></div></div>
    <Card><div className="flex flex-wrap items-end gap-3"><label className="text-sm">De<input type="date" className={fieldClass} value={start} onChange={(event) => setStart(event.target.value)}/></label><label className="text-sm">Até<input type="date" className={fieldClass} value={end} onChange={(event) => setEnd(event.target.value)}/></label><Button variant="secondary" onClick={() => { setStart(today); setEnd(today); }}>Hoje</Button><Button variant="secondary" onClick={() => { setStart(monthStart); setEnd(today); }}>Este mês</Button></div></Card>
    <div className="flex flex-wrap gap-2">{tabs.map(([key, label]) => <Button key={key} variant={tab === key ? "primary" : "secondary"} onClick={() => setTab(key)}>{label}</Button>)}</div>

    {tab === "resumo" && <><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{metrics.map(([label, value, Icon]) => <Card key={label}><div className="flex items-start justify-between"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-semibold">{formatCurrency(value)}</p></div><span className="rounded-2xl bg-brand/10 p-2 text-brand"><Icon size={18}/></span></div></Card>)}</div>
      <div className="grid gap-4 lg:grid-cols-3"><Card><h2 className="font-semibold">Resultado do período</h2><div className="mt-4 space-y-3 text-sm"><p className="flex justify-between"><span>CMV</span><strong>{formatCurrency(summary.cmv)}</strong></p><p className="flex justify-between"><span>Margem bruta</span><strong>{summary.gross_margin.toFixed(2)}%</strong></p><p className="flex justify-between"><span>Despesas operacionais</span><strong>{formatCurrency(summary.operational_expenses)}</strong></p><p className="flex justify-between"><span>Ticket médio</span><strong>{formatCurrency(summary.average_ticket)}</strong></p></div><p className="mt-4 text-xs text-slate-500">Visão gerencial estimada, não uma DRE contábil oficial.</p></Card>
      <Card><h2 className="font-semibold">Faturamento x recebimento</h2><div className="mt-4 space-y-3 text-sm"><p className="flex justify-between"><span>Vendas recebidas</span><strong>{formatCurrency(summary.received_sales)}</strong></p><p className="flex justify-between"><span>Vendas fiadas</span><strong>{formatCurrency(summary.credit_sales)}</strong></p><p className="flex justify-between"><span>Fiado recebido</span><strong>{formatCurrency(summary.credit_receipts)}</strong></p><p className="flex justify-between"><span>Outras receitas</span><strong>{formatCurrency(summary.manual_revenues)}</strong></p></div></Card>
      <Card><h2 className="font-semibold">Próximos compromissos</h2><div className="mt-4 space-y-4">{projections.map((item) => <div key={item.days} className="rounded-2xl bg-brand/5 p-3"><p className="text-sm font-medium">Próximos {item.days} dias</p><p className="mt-2 flex justify-between text-sm"><span>A pagar</span><strong>{formatCurrency(item.payables)}</strong></p><p className="mt-1 flex justify-between text-sm"><span>A receber</span><strong>{formatCurrency(item.receivables)}</strong></p></div>)}</div></Card></div></>}

    {tab === "pagar" && <Card>{!payables.length ? <EmptyState title="Nenhuma conta a pagar" description="Cadastre despesas e obrigações para acompanhar os vencimentos."/> : <DataTable headers={["Descrição", "Categoria", "Vencimento", "Valor", "Saldo", "Status", "Ação"]}>{payables.map((item) => <tr key={item.id}><td className="px-4 py-3"><p className="font-medium">{item.description}</p><p className="text-xs text-slate-500">{item.supplier_name || item.origin}</p></td><td className="px-4 py-3">{item.category_name}</td><td className="px-4 py-3">{formatDate(item.due_date)}</td><td className="px-4 py-3">{formatCurrency(item.original_amount)}</td><td className="px-4 py-3 font-medium">{formatCurrency(item.balance)}</td><td className="px-4 py-3"><Badge label={item.status}/></td><td className="px-4 py-3"><Button variant="ghost" disabled={item.balance <= 0 || item.status === "CANCELADA"} onClick={() => { setPaying(item); setPayment({ amount: String(item.balance), method: "PIX", use_cash_register: false }); }}>Pagar</Button></td></tr>)}</DataTable>}</Card>}

    {tab === "receber" && <Card>{!receivables.length ? <EmptyState title="Nenhuma conta a receber" description="Fiados e recebíveis futuros aparecerão aqui."/> : <DataTable headers={["Origem", "Cliente / descrição", "Vencimento", "Valor", "Recebido", "Saldo", "Status", "Ação"]}>{receivables.map((item) => <tr key={item.id}><td className="px-4 py-3">{item.source}</td><td className="px-4 py-3"><p className="font-medium">{item.customer_name || item.description}</p><p className="text-xs text-slate-500">{item.description}</p></td><td className="px-4 py-3">{item.due_date ? formatDate(item.due_date) : "Sem vencimento"}</td><td className="px-4 py-3">{formatCurrency(item.original_amount)}</td><td className="px-4 py-3">{formatCurrency(item.received_amount)}</td><td className="px-4 py-3 font-medium">{formatCurrency(item.balance)}</td><td className="px-4 py-3"><Badge label={item.status}/></td><td className="px-4 py-3">{item.source === "MANUAL" ? <Button variant="ghost" onClick={() => { setReceiving(item); setPayment({ amount: String(item.balance), method: "PIX", use_cash_register: false }); }}>Receber</Button> : <span className="text-xs text-slate-500">Receba em Clientes</span>}</td></tr>)}</DataTable>}</Card>}

    {tab === "fluxo" && <Card>{!flow.length ? <EmptyState title="Sem movimentações no período" description="As entradas e saídas financeiras aparecerão aqui."/> : <DataTable headers={["Data", "Tipo", "Origem", "Descrição", "Forma", "Valor"]}>{flow.map((item) => <tr key={item.id}><td className="px-4 py-3">{formatDateTime(item.occurred_at)}</td><td className={`px-4 py-3 font-medium ${item.direction === "ENTRADA" ? "text-emerald-700" : "text-rose-600"}`}>{item.direction}</td><td className="px-4 py-3">{item.source}</td><td className="px-4 py-3">{item.description}</td><td className="px-4 py-3">{item.payment_method}</td><td className="px-4 py-3 font-medium">{formatCurrency(item.amount)}</td></tr>)}</DataTable>}</Card>}

    {tab === "recorrentes" && <Card><div className="mb-4 flex justify-between"><div><h2 className="font-semibold">Despesas recorrentes</h2><p className="text-sm text-slate-500">Gere contas sem duplicar o mesmo período.</p></div><div className="flex gap-2"><Button variant="secondary" onClick={async () => { await financialService.generateRecurring(); await refresh(); toast.push("Contas recorrentes atualizadas."); }}><RefreshCw size={15} className="mr-1"/>Gerar agora</Button><Button onClick={() => setModal("recurring")}><CalendarClock size={15} className="mr-1"/>Nova recorrência</Button></div></div>{!recurring.length ? <EmptyState title="Nenhuma recorrência" description="Cadastre aluguel, internet e outros compromissos previsíveis."/> : <DataTable headers={["Descrição", "Periodicidade", "Próximo vencimento", "Valor", "Status"]}>{recurring.map((item) => <tr key={item.id}><td className="px-4 py-3 font-medium">{item.description}</td><td className="px-4 py-3">{item.frequency}</td><td className="px-4 py-3">{formatDate(item.next_due_date)}</td><td className="px-4 py-3">{formatCurrency(item.amount)}</td><td className="px-4 py-3"><Badge label={item.active ? "ATIVA" : "INATIVA"}/></td></tr>)}</DataTable>}</Card>}

    {modal === "payable" && <Modal title="Nova conta a pagar" onClose={() => setModal(null)}><form className="grid gap-4 md:grid-cols-2" onSubmit={submitPayable}><label className="text-sm md:col-span-2">Descrição<input required className={fieldClass} value={payableForm.description} onChange={(e) => setPayableForm({ ...payableForm, description: e.target.value })}/></label><label className="text-sm">Categoria<select required className={fieldClass} value={payableForm.category_id} onChange={(e) => setPayableForm({ ...payableForm, category_id: e.target.value })}><option value="">Selecione</option>{expenseCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm">Fornecedor<select className={fieldClass} value={payableForm.supplier_id} onChange={(e) => setPayableForm({ ...payableForm, supplier_id: e.target.value })}><option value="">Opcional</option>{suppliers.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm">Pedido de compra<select className={fieldClass} value={payableForm.purchase_order_id} onChange={(e) => setPayableForm({ ...payableForm, purchase_order_id: e.target.value })}><option value="">Sem pedido</option>{purchases.map((item) => <option key={item.id} value={item.id}>{item.number} · {item.supplier_name}</option>)}</select></label><label className="text-sm">Valor<input required type="number" min="0.01" step="0.01" className={fieldClass} value={payableForm.amount} onChange={(e) => setPayableForm({ ...payableForm, amount: e.target.value })}/></label><label className="text-sm">Vencimento<input required type="date" className={fieldClass} value={payableForm.due_date} onChange={(e) => setPayableForm({ ...payableForm, due_date: e.target.value })}/></label><label className="text-sm md:col-span-2">Observações<textarea className={fieldClass} value={payableForm.notes} onChange={(e) => setPayableForm({ ...payableForm, notes: e.target.value })}/></label><Button className="md:col-span-2">Salvar conta</Button></form></Modal>}
    {modal === "revenue" && <Modal title="Nova receita manual" onClose={() => setModal(null)}><form className="grid gap-4 md:grid-cols-2" onSubmit={submitRevenue}><label className="text-sm md:col-span-2">Descrição<input required className={fieldClass} value={revenueForm.description} onChange={(e) => setRevenueForm({ ...revenueForm, description: e.target.value })}/></label><label className="text-sm">Categoria<select required className={fieldClass} value={revenueForm.category_id} onChange={(e) => setRevenueForm({ ...revenueForm, category_id: e.target.value })}><option value="">Selecione</option>{revenueCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm">Forma<select className={fieldClass} value={revenueForm.payment_method} onChange={(e) => setRevenueForm({ ...revenueForm, payment_method: e.target.value })}><option>DINHEIRO</option><option>PIX</option><option>DEBITO</option><option>CREDITO</option></select></label><label className="text-sm">Valor<input required type="number" min="0.01" step="0.01" className={fieldClass} value={revenueForm.amount} onChange={(e) => setRevenueForm({ ...revenueForm, amount: e.target.value })}/></label><label className="text-sm md:col-span-2">Observações<textarea className={fieldClass} value={revenueForm.notes} onChange={(e) => setRevenueForm({ ...revenueForm, notes: e.target.value })}/></label><Button className="md:col-span-2">Registrar receita</Button></form></Modal>}
    {modal === "recurring" && <Modal title="Nova despesa recorrente" onClose={() => setModal(null)}><form className="grid gap-4 md:grid-cols-2" onSubmit={submitRecurring}><label className="text-sm md:col-span-2">Descrição<input required className={fieldClass} value={recurringForm.description} onChange={(e) => setRecurringForm({ ...recurringForm, description: e.target.value })}/></label><label className="text-sm">Categoria<select required className={fieldClass} value={recurringForm.category_id} onChange={(e) => setRecurringForm({ ...recurringForm, category_id: e.target.value })}><option value="">Selecione</option>{expenseCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label><label className="text-sm">Periodicidade<select className={fieldClass} value={recurringForm.frequency} onChange={(e) => setRecurringForm({ ...recurringForm, frequency: e.target.value })}><option value="SEMANAL">Semanal</option><option value="MENSAL">Mensal</option><option value="ANUAL">Anual</option></select></label><label className="text-sm">Valor<input required type="number" min="0.01" step="0.01" className={fieldClass} value={recurringForm.amount} onChange={(e) => setRecurringForm({ ...recurringForm, amount: e.target.value })}/></label><label className="text-sm">Próximo vencimento<input required type="date" className={fieldClass} value={recurringForm.next_due_date} onChange={(e) => setRecurringForm({ ...recurringForm, next_due_date: e.target.value })}/></label><Button className="md:col-span-2">Salvar recorrência</Button></form></Modal>}
    {(paying || receiving) && <Modal title={paying ? `Pagar ${paying.description}` : `Receber ${receiving?.description}`} onClose={() => { setPaying(null); setReceiving(null); }}><form className="grid gap-4 md:grid-cols-2" onSubmit={submitPayment}><label className="text-sm">Valor<input required type="number" min="0.01" max={paying?.balance ?? receiving?.balance} step="0.01" className={fieldClass} value={payment.amount} onChange={(e) => setPayment({ ...payment, amount: e.target.value })}/></label><label className="text-sm">Forma<select className={fieldClass} value={payment.method} onChange={(e) => setPayment({ ...payment, method: e.target.value })}><option>DINHEIRO</option><option>PIX</option><option>DEBITO</option><option>CREDITO</option></select></label>{paying && payment.method === "DINHEIRO" && <label className="flex items-center gap-2 text-sm md:col-span-2"><input type="checkbox" checked={payment.use_cash_register} onChange={(e) => setPayment({ ...payment, use_cash_register: e.target.checked })}/>Retirar do caixa físico aberto</label>}<Button className="md:col-span-2"><Banknote size={15} className="mr-2"/>Confirmar</Button></form></Modal>}
  </div>;
}
