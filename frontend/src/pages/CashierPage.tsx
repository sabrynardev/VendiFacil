import { Clock3, Minus, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useAuth } from "../contexts/AuthContext";
import { useConnectivity } from "../contexts/ConnectivityContext";
import { useHotkeys } from "../hooks/useHotkeys";
import { cashRegisterService } from "../services/cashRegisters";
import { catalogService } from "../services/catalog";
import { salesService } from "../services/sales";
import { customerService } from "../services/management";
import { ApiError } from "../services/api";
import { allDrafts, applyPendingStock, cacheProducts, findCachedProduct, getDeviceId, getDraft, getSession, queueOperation, removeDraft, saveDraft, saveSession, type OfflineDraft, type OfflineSalePayload } from "../services/offlineDb";
import type { CashRegister, Customer, Product, Sale } from "../types";
import { formatCurrency } from "../utils/format";

type CartItem = { product: Product; quantity: number; discount: number };
type Payment = { method: string; amount: number; amount_received?: number };

export function CashierPage() {
  const toast = useToast();
  const { user } = useAuth();
  const connectivity = useConnectivity();
  const inputRef = useRef<HTMLInputElement>(null);
  const [register, setRegister] = useState<CashRegister | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [discount, setDiscount] = useState(0);
  const [surcharge, setSurcharge] = useState(0);
  const [note, setNote] = useState("");
  const [payments, setPayments] = useState<Payment[]>([{ method: "PIX", amount: 0 }]);
  const [checkout, setCheckout] = useState(false);
  const [cashModal, setCashModal] = useState<"open" | "withdrawal" | "supply" | "close" | null>(null);
  const [cashValue, setCashValue] = useState(0);
  const [cashReason, setCashReason] = useState("");
  const [held, setHeld] = useState<Sale[]>([]);
  const [heldId, setHeldId] = useState<number | null>(null);
  const [receipt, setReceipt] = useState<Sale | null>(null);
  const [authorizationEmail, setAuthorizationEmail] = useState("");
  const [authorizationPassword, setAuthorizationPassword] = useState("");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [customerId, setCustomerId] = useState(0);
  const [creditDueDate, setCreditDueDate] = useState("");
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const [localHeld, setLocalHeld] = useState<OfflineDraft[]>([]);
  const [draftReady, setDraftReady] = useState(false);

  const draftKey = user ? `current:${user.account_id}:${user.id}` : "";

  useEffect(() => { if (user) void restoreOfflineState(); }, [user?.id]);
  useEffect(() => {
    if (!draftReady || !user || !draftKey) return;
    if (!cart.length) { void removeDraft(draftKey); return; }
    const timer = window.setTimeout(() => void saveDraft({ key: draftKey, account_id: user.account_id, user_id: user.id, cart, discount, surcharge, note, customer_id: customerId || undefined, kind: "CURRENT", updated_at: new Date().toISOString() }), 250);
    return () => window.clearTimeout(timer);
  }, [cart, discount, surcharge, note, customerId, draftReady, draftKey, user?.id]);
  useEffect(() => { inputRef.current?.focus(); }, [cart.length]);
  useHotkeys({ f2: () => inputRef.current?.focus(), f4: () => cart.length > 0 && register && setCheckout(true), escape: () => setCheckout(false) });

  const itemsSubtotal = cart.reduce((sum, item) => sum + item.product.sale_price * item.quantity - item.discount, 0);
  const grossTotal = cart.reduce((sum, item) => sum + item.product.sale_price * item.quantity, 0);
  const totalDiscount = cart.reduce((sum, item) => sum + item.discount, 0) + discount;
  const requiresAuthorization = grossTotal > 0 && totalDiscount / grossTotal > 0.1 && !user?.permissions.includes("discount.special");
  const total = Math.max(Math.round((itemsSubtotal - discount + surcharge) * 100) / 100, 0);
  const paid = payments.reduce((sum, payment) => sum + Number(payment.amount || 0), 0);
  const change = payments.reduce((sum, payment) => payment.method === "DINHEIRO" ? sum + Math.max(Number(payment.amount_received || 0) - Number(payment.amount || 0), 0) : sum, 0);
  const creditAmount = payments.reduce((sum, payment) => payment.method === "FIADO" ? sum + Number(payment.amount || 0) : sum, 0);
  const selectedCustomer = customers.find((customer) => customer.id === customerId);
  const requiresCreditAuthorization = creditAmount > 0 && selectedCustomer?.credit_limit != null && selectedCustomer.balance + creditAmount > selectedCustomer.credit_limit && !user?.permissions.includes("credit.manage");
  const needsManagerAuthorization = requiresAuthorization || requiresCreditAuthorization;

  async function loadLocalHeld() {
    if (!user) return;
    setLocalHeld((await allDrafts()).filter(item => item.account_id === user.account_id && item.user_id === user.id && item.kind === "HELD"));
  }

  async function restoreOfflineState() {
    if (!user) return;
    const saved = await getDraft(`current:${user.account_id}:${user.id}`);
    if (saved?.cart.length) {
      setCart(saved.cart); setDiscount(saved.discount); setSurcharge(saved.surcharge); setNote(saved.note); setCustomerId(saved.customer_id ?? 0);
      toast.push("Carrinho anterior recuperado neste dispositivo.");
    }
    await loadLocalHeld();
    try { await refreshOperation(); }
    catch (err) { setError(err instanceof Error ? err.message : "Não foi possível carregar a operação."); }
    finally { setDraftReady(true); }
  }

  async function refreshOperation() {
    if (!user) return;
    try {
      const [current, waiting, customerList, products] = await Promise.all([cashRegisterService.current(), salesService.list({ status: "ON_HOLD" }), customerService.list(), catalogService.listProducts()]);
      setRegister(current); setHeld(waiting); setCustomers(customerList);
      await Promise.all([cacheProducts(user.account_id, products), saveSession({ key: `session:${user.account_id}:${user.id}`, account_id: user.account_id, user_id: user.id, cached_at: new Date().toISOString(), register: current })]);
    } catch (err) {
      if (!(err instanceof ApiError) || err.response.status !== 0) throw err;
      const session = await getSession(`session:${user.account_id}:${user.id}`);
      const valid = session && Date.now() - new Date(session.cached_at).getTime() <= 12 * 60 * 60 * 1000;
      setRegister(valid ? session.register : null);
    }
  }

  async function addProduct() {
    if (!query.trim()) return;
    try {
      let product: Product | undefined;
      try { product = connectivity.status === "OFFLINE" && user ? await findCachedProduct(user.account_id, query.trim()) : await catalogService.getProductByBarcode(query.trim()); }
      catch (err) {
        if (!(err instanceof ApiError) || err.response.status !== 0 || !user) throw err;
        product = await findCachedProduct(user.account_id, query.trim());
      }
      if (!product) throw new Error("Produto não encontrado.");
      const increment = product.unit === "UN" ? 1 : 0.1;
      setCart((current) => {
        const existing = current.find((item) => item.product.id === product.id);
        return existing ? current.map((item) => item.product.id === product.id ? { ...item, quantity: item.quantity + increment } : item) : [...current, { product, quantity: increment, discount: 0 }];
      });
      setQuery(""); toast.push(`${product.name} adicionado ao carrinho.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Produto não encontrado."); }
  }

  function updateQuantity(id: number, value: number) {
    setCart((current) => current.map((item) => item.product.id === id ? { ...item, quantity: Math.max(value, item.product.unit === "UN" ? 1 : 0.001) } : item));
  }

  async function submitCashOperation() {
    setProcessing(true);
    try {
      let updated: CashRegister;
      if (cashModal === "open") updated = await cashRegisterService.open(cashValue);
      else if (cashModal === "withdrawal") updated = await cashRegisterService.withdrawal(cashValue, cashReason);
      else if (cashModal === "supply") updated = await cashRegisterService.supply(cashValue, cashReason);
      else updated = await cashRegisterService.close(cashValue, cashReason);
      setRegister(updated.status === "OPEN" ? updated : null);
      toast.push(cashModal === "close" ? "Caixa fechado com sucesso." : "Operação de caixa registrada.");
      setCashModal(null); setCashValue(0); setCashReason("");
    } catch (err) { setError(err instanceof Error ? err.message : "Não foi possível registrar a operação."); }
    finally { setProcessing(false); }
  }

  async function putOnHold() {
    if (!cart.length) return;
    if (connectivity.status === "OFFLINE") { await putOnHoldOffline(); return; }
    try {
      await salesService.hold({ items: cart.map((i) => ({ product_id: i.product.id, quantity: i.quantity, discount: i.discount })), discount, surcharge, note, customer_id: customerId || undefined });
      clearSale(); await refreshOperation(); toast.push("Venda colocada em espera.");
    } catch (err) {
      if (!(err instanceof ApiError) || err.response.status !== 0 || !user) { setError(err instanceof Error ? err.message : "Não foi possível colocar a venda em espera."); return; }
      await putOnHoldOffline();
    }
  }

  async function putOnHoldOffline() {
    if (!user) return;
    await saveDraft({ key: `held:${user.account_id}:${user.id}:${crypto.randomUUID()}`, account_id: user.account_id, user_id: user.id, cart, discount, surcharge, note, customer_id: customerId || undefined, kind: "HELD", updated_at: new Date().toISOString() });
    clearSale(); await loadLocalHeld(); toast.push("Venda guardada neste dispositivo.");
  }

  function recover(sale: Sale) {
    setCart(sale.items.map((item) => ({ product: { id: item.product_id, name: item.product_name, unit: item.product_unit, sale_price: item.unit_price } as Product, quantity: item.quantity, discount: item.discount })));
    setDiscount(sale.discount); setSurcharge(sale.surcharge); setNote(sale.note ?? ""); setHeldId(sale.id); toast.push("Venda recuperada.");
    setCustomerId(sale.customer_id ?? 0);
  }

  async function cancelHeld(sale: Sale) {
    try {
      await salesService.cancel(sale.id, "Venda em espera descartada pelo operador");
      if (heldId === sale.id) clearSale();
      await refreshOperation();
      toast.push("Venda em espera cancelada.");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Não foi possível cancelar a venda em espera.", "error");
    }
  }

  function recoverLocal(draft: OfflineDraft) {
    setCart(draft.cart); setDiscount(draft.discount); setSurcharge(draft.surcharge); setNote(draft.note); setCustomerId(draft.customer_id ?? 0);
    void removeDraft(draft.key).then(loadLocalHeld);
    toast.push("Venda offline recuperada.");
  }

  async function cancelLocalHeld(draft: OfflineDraft) {
    await removeDraft(draft.key); await loadLocalHeld(); toast.push("Venda em espera descartada.");
  }

  function clearSale() { setCart([]); setDiscount(0); setSurcharge(0); setNote(""); setHeldId(null); setPayments([{ method: "PIX", amount: 0 }]); setAuthorizationEmail(""); setAuthorizationPassword(""); setCustomerId(0); setCreditDueDate(""); if (draftKey) void removeDraft(draftKey); }

  async function finalizeOffline(idempotencyKey: string) {
    if (!user || !register) throw new Error("É necessário ter uma sessão de caixa válida salva neste dispositivo.");
    if (heldId) throw new Error("Uma venda em espera do servidor precisa de conexão para ser concluída.");
    if (payments.some(payment => payment.method === "FIADO")) throw new Error("Venda fiada exige conexão para validar limite e saldo.");
    if (needsManagerAuthorization) throw new Error("Esta venda exige autorização online de gerente.");
    const operationId = crypto.randomUUID();
    const payload: OfflineSalePayload = {
      operation_id: operationId, idempotency_key: idempotencyKey, device_id: getDeviceId(), local_created_at: new Date().toISOString(), cash_register_id: register.id,
      items: cart.map(item => ({ product_id: item.product.id, quantity: item.quantity, discount: item.discount, unit_price: item.product.sale_price, product_updated_at: item.product.updated_at })),
      discount, surcharge, payments, note,
    };
    for (const item of cart) {
      if (item.quantity > item.product.stock_quantity) throw new Error(`Estoque local insuficiente para ${item.product.name}. Disponível: ${item.product.stock_quantity}.`);
    }
    await queueOperation({ operation_id: operationId, account_id: user.account_id, user_id: user.id, type: "SALE", payload, created_at: payload.local_created_at, attempts: 0, status: "PENDING" });
    await applyPendingStock(user.account_id, payload.items, 1);
    const offlineReceipt: Sale = {
      id: -Date.now(), number: "PENDENTE", user_id: user.id, operator_name: user.name, cash_register_id: register.id,
      subtotal: itemsSubtotal, discount, surcharge, total, payment_method: payments.map(payment => payment.method).join("+"), amount_received: payments.reduce((sum, payment) => sum + Number(payment.amount_received ?? payment.amount), 0), change_amount: change,
      status: "PENDENTE_SINCRONIZACAO", note, created_at: payload.local_created_at,
      items: cart.map((item, index) => ({ id: -(index + 1), product_id: item.product.id, product_name: item.product.name, product_unit: item.product.unit, quantity: item.quantity, unit_price: item.product.sale_price, discount: item.discount, subtotal: item.product.sale_price * item.quantity - item.discount })),
      payments: payments.map((payment, index) => ({ id: -(index + 1), method: payment.method, amount: payment.amount, amount_received: payment.amount_received, change_amount: payment.method === "DINHEIRO" ? Math.max(Number(payment.amount_received ?? payment.amount) - payment.amount, 0) : 0 })),
    };
    setReceipt(offlineReceipt); clearSale(); setCheckout(false); await connectivity.checkNow(); toast.push("Venda salva com segurança. Ela será sincronizada automaticamente.");
  }

  async function finalize() {
    setProcessing(true); setError("");
    const idempotencyKey = crypto.randomUUID();
    try {
      if (connectivity.status === "OFFLINE") { await finalizeOffline(idempotencyKey); return; }
      const payload = { items: cart.map((i) => ({ product_id: i.product.id, quantity: i.quantity, discount: i.discount })), discount, surcharge, payments, note, idempotency_key: idempotencyKey, authorization_email: authorizationEmail || undefined, authorization_password: authorizationPassword || undefined, customer_id: customerId || undefined, credit_due_date: creditDueDate || undefined };
      const sale = heldId ? await salesService.completeHeld(heldId, payload) : await salesService.create(payload);
      setReceipt(sale); clearSale(); setCheckout(false); await refreshOperation(); toast.push("Venda concluída com sucesso.");
    } catch (err) {
      if (err instanceof ApiError && err.response.status === 0) {
        try { await finalizeOffline(idempotencyKey); }
        catch (offlineError) { setError(offlineError instanceof Error ? offlineError.message : "Não foi possível guardar a venda offline."); }
      } else setError(err instanceof Error ? err.message : "Não foi possível finalizar a venda.");
    }
    finally { setProcessing(false); }
  }

  return <div className="grid gap-6 xl:grid-cols-[1.6fr_0.8fr]">
    <div className="space-y-6">
      <Card className="overflow-hidden p-0"><div className="bg-[linear-gradient(120deg,#011142,#01258F)] px-6 py-6 text-white"><p className="text-xs uppercase tracking-[0.35em] text-blue-200">Frente de Caixa</p><h1 className="mt-3 text-3xl font-semibold">Venda rápida com foco total em operação.</h1><p className="mt-3 text-sm text-blue-100">{register ? `Caixa #${register.id} aberto por ${register.operator_name}` : "Abra o caixa para começar a vender."}</p></div></Card>
      {connectivity.status === "OFFLINE" && <Card className="border-amber-200 bg-amber-50"><p className="text-sm font-medium text-amber-900">Modo offline ativo</p><p className="mt-1 text-xs text-amber-700">Vendas comuns ficam salvas neste dispositivo e serão enviadas automaticamente. Fiado e operações de caixa aguardam a conexão.</p></Card>}
      {!register ? <Card><EmptyState title="Nenhum caixa aberto" description="Informe o saldo inicial para iniciar a operação." /><Button className="mt-4 w-full" onClick={() => setCashModal("open")}>Abrir caixa</Button></Card> : <>
        <Card><div className="flex gap-3"><div className="relative flex-1"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input ref={inputRef} className="w-full rounded-2xl border-stroke bg-white py-4 pl-11 text-brandDeeper" placeholder="Código de barras, nome ou SKU" value={query} onChange={(e)=>setQuery(e.target.value)} onKeyDown={(e)=>{if(e.key==="Enter"){e.preventDefault();void addProduct();}}}/></div><Button onClick={()=>void addProduct()}>Adicionar</Button></div>{error&&<p className="mt-3 text-sm text-rose-600">{error}</p>}</Card>
        <Card><div className="mb-4 flex justify-between"><h2 className="text-lg font-semibold">Carrinho</h2><span className="text-xs text-slate-500">F2 buscar · F4 finalizar · ESC fechar</span></div>{!cart.length?<EmptyState title="Carrinho vazio" description="Escaneie ou pesquise um produto."/>:<div className="space-y-3">{cart.map((item)=><div key={item.product.id} className="grid gap-3 rounded-2xl border border-stroke bg-brand/4 p-4 md:grid-cols-[2fr_1fr_1fr_1fr]"><div><p className="font-medium">{item.product.name}</p><p className="text-xs text-slate-500">{formatCurrency(item.product.sale_price)}/{item.product.unit}</p></div><div className="flex items-center"><Button variant="ghost" onClick={()=>updateQuantity(item.product.id,item.quantity-(item.product.unit==="UN"?1:0.1))}><Minus size={15}/></Button><input type="number" min="0.001" step={item.product.unit==="UN"?1:0.001} className="w-20 rounded-xl border-stroke bg-white text-center" value={item.quantity} onChange={(e)=>updateQuantity(item.product.id,Number(e.target.value))}/><Button variant="ghost" onClick={()=>updateQuantity(item.product.id,item.quantity+(item.product.unit==="UN"?1:0.1))}><Plus size={15}/></Button></div><input aria-label={`Desconto ${item.product.name}`} type="number" min="0" step="0.01" className="rounded-xl border-stroke bg-white" value={item.discount} onChange={(e)=>setCart(c=>c.map(i=>i.product.id===item.product.id?{...i,discount:Number(e.target.value)}:i))}/><div className="flex items-center justify-between"><b>{formatCurrency(item.product.sale_price*item.quantity-item.discount)}</b><Button variant="ghost" onClick={()=>setCart(c=>c.filter(i=>i.product.id!==item.product.id))}><Trash2 size={16}/></Button></div></div>)}</div>}</Card>
      </>}
    </div>
    <div className="space-y-6">{register&&<Card><p className="text-sm text-slate-500">Total da venda</p><p className="mt-2 text-4xl font-semibold">{formatCurrency(total)}</p><div className="mt-5 grid gap-3"><label className="text-sm">Cliente opcional<select className="mt-1 w-full rounded-xl border-stroke bg-white" value={customerId} onChange={(e)=>setCustomerId(Number(e.target.value))}><option value={0}>Consumidor não identificado</option>{customers.map(customer=><option key={customer.id} value={customer.id}>{customer.name}{customer.balance?` · saldo ${formatCurrency(customer.balance)}`:""}</option>)}</select></label><label className="text-sm">Desconto geral<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={discount} onChange={(e)=>setDiscount(Number(e.target.value))}/></label><label className="text-sm">Acréscimo<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={surcharge} onChange={(e)=>setSurcharge(Number(e.target.value))}/></label><label className="text-sm">Observação<input className="mt-1 w-full rounded-xl border-stroke bg-white" value={note} onChange={(e)=>setNote(e.target.value)}/></label></div><Button className="mt-5 w-full" disabled={!cart.length} onClick={()=>{setPayments([{method:"PIX",amount:total}]);setCheckout(true)}}>FINALIZAR VENDA</Button><Button variant="secondary" className="mt-2 w-full" disabled={!cart.length} onClick={()=>void putOnHold()}><Clock3 size={16} className="mr-2"/>Colocar em espera</Button></Card>}
      {register&&<Card><h2 className="font-semibold">Operações do caixa</h2><p className="mt-2 text-sm text-slate-500">Dinheiro esperado: {formatCurrency(register.summary.expected_cash)}</p><div className="mt-4 grid grid-cols-2 gap-2"><Button variant="secondary" disabled={connectivity.status === "OFFLINE"} onClick={()=>setCashModal("withdrawal")}>Sangria</Button><Button variant="secondary" disabled={connectivity.status === "OFFLINE"} onClick={()=>setCashModal("supply")}>Suprimento</Button><Button className="col-span-2" disabled={connectivity.status === "OFFLINE"} onClick={()=>{setCashValue(register.summary.expected_cash);setCashModal("close")}}>Fechar caixa</Button></div>{connectivity.status === "OFFLINE"&&<p className="mt-3 text-xs text-slate-500">Sangria, suprimento e fechamento exigem conexão.</p>}</Card>}
      <Card><h2 className="font-semibold">Vendas em espera</h2>{!held.length&&!localHeld.length?<p className="mt-3 text-sm text-slate-500">Nenhuma venda em espera no momento.</p>:<>{held.map(s=><div key={s.id} className="mt-3 flex items-center gap-2 rounded-xl border border-stroke p-2"><button className="flex flex-1 justify-between p-1 text-left" onClick={()=>recover(s)}><span>{s.number}</span><b>{formatCurrency(s.total)}</b></button><Button variant="ghost" aria-label={`Cancelar ${s.number}`} onClick={()=>void cancelHeld(s)}><Trash2 size={16}/></Button></div>)}{localHeld.map(draft=><div key={draft.key} className="mt-3 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-2"><button className="flex flex-1 justify-between p-1 text-left" onClick={()=>recoverLocal(draft)}><span>Salva neste dispositivo</span><b>{formatCurrency(draft.cart.reduce((sum,item)=>sum+item.product.sale_price*item.quantity-item.discount,0)-draft.discount+draft.surcharge)}</b></button><Button variant="ghost" aria-label="Descartar venda offline em espera" onClick={()=>void cancelLocalHeld(draft)}><Trash2 size={16}/></Button></div>)}</>}</Card>
    </div>
    {checkout&&<Modal title="Finalizar venda" onClose={()=>setCheckout(false)}><div className="space-y-4"><p className="text-3xl font-semibold">{formatCurrency(total)}</p>{payments.map((payment,index)=><div key={index} className="grid gap-2 md:grid-cols-3"><select className="rounded-xl border-stroke bg-white" value={payment.method} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,method:e.target.value}:x))}>{["DINHEIRO","PIX","DEBITO","CREDITO","FIADO"].map(m=><option key={m}>{m}</option>)}</select><input aria-label="Valor do pagamento" type="number" step="0.01" className="rounded-xl border-stroke bg-white" value={payment.amount} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,amount:Number(e.target.value)}:x))}/>{payment.method==="DINHEIRO"?<input aria-label="Valor recebido" type="number" step="0.01" placeholder="Recebido" className="rounded-xl border-stroke bg-white" value={payment.amount_received??payment.amount} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,amount_received:Number(e.target.value)}:x))}/>:<Button variant="ghost" onClick={()=>setPayments(p=>p.filter((_,i)=>i!==index))}>Remover</Button>}</div>)}<Button variant="secondary" onClick={()=>setPayments(p=>[...p,{method:"PIX",amount:Math.max(total-paid,0)}])}>Adicionar pagamento</Button><div className="flex justify-between text-sm"><span>Total informado: {formatCurrency(paid)}</span><span>Troco: {formatCurrency(change)}</span></div>{creditAmount>0&&<Card className="bg-brand/4"><p className="text-sm font-medium">Venda fiada: {formatCurrency(creditAmount)}</p>{selectedCustomer?<p className="mt-1 text-xs text-slate-500">{selectedCustomer.name} · saldo atual {formatCurrency(selectedCustomer.balance)}{selectedCustomer.credit_limit!=null?` · limite ${formatCurrency(selectedCustomer.credit_limit)}`:" · sem limite definido"}</p>:<p className="mt-1 text-sm text-rose-600">Selecione um cliente para usar fiado.</p>}<label className="mt-3 block text-sm">Vencimento opcional<input type="date" className="mt-1 w-full rounded-xl border-stroke bg-white" value={creditDueDate} onChange={(e)=>setCreditDueDate(e.target.value)}/></label>{selectedCustomer?.credit_blocked&&<p className="mt-2 text-sm text-rose-600">O fiado deste cliente está bloqueado.</p>}</Card>}{needsManagerAuthorization&&<Card className="bg-amber-50"><p className="mb-3 text-sm font-medium text-amber-800">{requiresCreditAuthorization?"O limite de crédito será excedido.":"Desconto acima de 10%."} Informe um gerente ou administrador.</p><div className="grid gap-2 md:grid-cols-2"><input type="email" placeholder="E-mail do autorizador" className="rounded-xl border-stroke bg-white" value={authorizationEmail} onChange={(e)=>setAuthorizationEmail(e.target.value)}/><input type="password" placeholder="Senha do autorizador" className="rounded-xl border-stroke bg-white" value={authorizationPassword} onChange={(e)=>setAuthorizationPassword(e.target.value)}/></div></Card>}{error&&<p className="text-sm text-rose-600">{error}</p>}<Button className="w-full" disabled={processing||Math.abs(paid-total)>0.009||(creditAmount>0&&(!customerId||selectedCustomer?.credit_blocked))||(needsManagerAuthorization&&(!authorizationEmail||!authorizationPassword))} onClick={()=>void finalize()}>{processing?"Confirmando...":"CONFIRMAR VENDA"}</Button></div></Modal>}
    {cashModal&&<Modal title={cashModal==="open"?"Abrir caixa":cashModal==="close"?"Fechar caixa":cashModal==="withdrawal"?"Sangria":"Suprimento"} onClose={()=>setCashModal(null)}><div className="space-y-4"><label className="block text-sm">{cashModal==="close"?"Valor físico contado":"Valor"}<input type="number" min="0" step="0.01" className="mt-2 w-full rounded-xl border-stroke bg-white" value={cashValue} onChange={(e)=>setCashValue(Number(e.target.value))}/></label>{cashModal!=="open"&&<label className="block text-sm">Motivo/observação<input className="mt-2 w-full rounded-xl border-stroke bg-white" value={cashReason} onChange={(e)=>setCashReason(e.target.value)}/></label>}<Button className="w-full" disabled={processing||(cashModal!=="open"&&!cashReason.trim())} onClick={()=>void submitCashOperation()}>Confirmar</Button></div></Modal>}
    {receipt&&<Modal title={`Comprovante ${receipt.number}`} onClose={()=>setReceipt(null)}><div id="receipt" className="space-y-3"><p className="text-center text-xl font-semibold">Vendi</p>{receipt.status==="PENDENTE_SINCRONIZACAO"&&<p className="rounded-xl bg-amber-50 p-2 text-center text-xs text-amber-800">Registro local pendente de confirmação do servidor. Não é documento fiscal.</p>}{receipt.customer_name&&<p className="text-center text-sm">Cliente: {receipt.customer_name}</p>}{receipt.items.map(i=><div key={i.id} className="flex justify-between text-sm"><span>{i.quantity}x {i.product_name}</span><span>{formatCurrency(i.subtotal)}</span></div>)}<div className="border-t border-stroke pt-3"><div className="flex justify-between font-semibold"><span>Total</span><span>{formatCurrency(receipt.total)}</span></div><p className="mt-2 text-sm">Pagamento: {receipt.payment_method}</p><p className="text-sm">Troco: {formatCurrency(receipt.change_amount??0)}</p></div><Button className="w-full print:hidden" onClick={()=>window.print()}>Imprimir comprovante</Button></div></Modal>}
  </div>;
}
