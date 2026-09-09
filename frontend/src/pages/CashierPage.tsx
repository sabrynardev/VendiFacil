import { Clock3, Minus, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useAuth } from "../contexts/AuthContext";
import { useHotkeys } from "../hooks/useHotkeys";
import { cashRegisterService } from "../services/cashRegisters";
import { catalogService } from "../services/catalog";
import { salesService } from "../services/sales";
import type { CashRegister, Product, Sale } from "../types";
import { formatCurrency } from "../utils/format";

type CartItem = { product: Product; quantity: number; discount: number };
type Payment = { method: string; amount: number; amount_received?: number };

export function CashierPage() {
  const toast = useToast();
  const { user } = useAuth();
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
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { void refreshOperation(); }, []);
  useEffect(() => { inputRef.current?.focus(); }, [cart.length]);
  useHotkeys({ f2: () => inputRef.current?.focus(), f4: () => cart.length > 0 && register && setCheckout(true), escape: () => setCheckout(false) });

  const itemsSubtotal = cart.reduce((sum, item) => sum + item.product.sale_price * item.quantity - item.discount, 0);
  const grossTotal = cart.reduce((sum, item) => sum + item.product.sale_price * item.quantity, 0);
  const totalDiscount = cart.reduce((sum, item) => sum + item.discount, 0) + discount;
  const requiresAuthorization = grossTotal > 0 && totalDiscount / grossTotal > 0.1 && !user?.permissions.includes("discount.special");
  const total = Math.max(Math.round((itemsSubtotal - discount + surcharge) * 100) / 100, 0);
  const paid = payments.reduce((sum, payment) => sum + Number(payment.amount || 0), 0);
  const change = payments.reduce((sum, payment) => payment.method === "DINHEIRO" ? sum + Math.max(Number(payment.amount_received || 0) - Number(payment.amount || 0), 0) : sum, 0);

  async function refreshOperation() {
    const [current, waiting] = await Promise.all([cashRegisterService.current(), salesService.list({ status: "ON_HOLD" })]);
    setRegister(current); setHeld(waiting);
  }

  async function addProduct() {
    if (!query.trim()) return;
    try {
      const product = await catalogService.getProductByBarcode(query.trim());
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
    await salesService.hold({ items: cart.map((i) => ({ product_id: i.product.id, quantity: i.quantity, discount: i.discount })), discount, surcharge, note });
    clearSale(); await refreshOperation(); toast.push("Venda colocada em espera.");
  }

  function recover(sale: Sale) {
    setCart(sale.items.map((item) => ({ product: { id: item.product_id, name: item.product_name, unit: item.product_unit, sale_price: item.unit_price } as Product, quantity: item.quantity, discount: item.discount })));
    setDiscount(sale.discount); setSurcharge(sale.surcharge); setNote(sale.note ?? ""); setHeldId(sale.id); toast.push("Venda recuperada.");
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

  function clearSale() { setCart([]); setDiscount(0); setSurcharge(0); setNote(""); setHeldId(null); setPayments([{ method: "PIX", amount: 0 }]); setAuthorizationEmail(""); setAuthorizationPassword(""); }

  async function finalize() {
    setProcessing(true); setError("");
    try {
      const payload = { items: cart.map((i) => ({ product_id: i.product.id, quantity: i.quantity, discount: i.discount })), discount, surcharge, payments, note, idempotency_key: crypto.randomUUID(), authorization_email: authorizationEmail || undefined, authorization_password: authorizationPassword || undefined };
      const sale = heldId ? await salesService.completeHeld(heldId, payload) : await salesService.create(payload);
      setReceipt(sale); clearSale(); setCheckout(false); await refreshOperation(); toast.push("Venda concluída com sucesso.");
    } catch (err) { setError(err instanceof Error ? err.message : "Não foi possível finalizar a venda."); }
    finally { setProcessing(false); }
  }

  return <div className="grid gap-6 xl:grid-cols-[1.6fr_0.8fr]">
    <div className="space-y-6">
      <Card className="overflow-hidden p-0"><div className="bg-[linear-gradient(120deg,#011142,#01258F)] px-6 py-6 text-white"><p className="text-xs uppercase tracking-[0.35em] text-blue-200">Frente de Caixa</p><h1 className="mt-3 text-3xl font-semibold">Venda rápida com foco total em operação.</h1><p className="mt-3 text-sm text-blue-100">{register ? `Caixa #${register.id} aberto por ${register.operator_name}` : "Abra o caixa para começar a vender."}</p></div></Card>
      {!register ? <Card><EmptyState title="Nenhum caixa aberto" description="Informe o saldo inicial para iniciar a operação." /><Button className="mt-4 w-full" onClick={() => setCashModal("open")}>Abrir caixa</Button></Card> : <>
        <Card><div className="flex gap-3"><div className="relative flex-1"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18}/><input ref={inputRef} className="w-full rounded-2xl border-stroke bg-white py-4 pl-11 text-brandDeeper" placeholder="Código de barras, nome ou SKU" value={query} onChange={(e)=>setQuery(e.target.value)} onKeyDown={(e)=>{if(e.key==="Enter"){e.preventDefault();void addProduct();}}}/></div><Button onClick={()=>void addProduct()}>Adicionar</Button></div>{error&&<p className="mt-3 text-sm text-rose-600">{error}</p>}</Card>
        <Card><div className="mb-4 flex justify-between"><h2 className="text-lg font-semibold">Carrinho</h2><span className="text-xs text-slate-500">F2 buscar · F4 finalizar · ESC fechar</span></div>{!cart.length?<EmptyState title="Carrinho vazio" description="Escaneie ou pesquise um produto."/>:<div className="space-y-3">{cart.map((item)=><div key={item.product.id} className="grid gap-3 rounded-2xl border border-stroke bg-brand/4 p-4 md:grid-cols-[2fr_1fr_1fr_1fr]"><div><p className="font-medium">{item.product.name}</p><p className="text-xs text-slate-500">{formatCurrency(item.product.sale_price)}/{item.product.unit}</p></div><div className="flex items-center"><Button variant="ghost" onClick={()=>updateQuantity(item.product.id,item.quantity-(item.product.unit==="UN"?1:0.1))}><Minus size={15}/></Button><input type="number" min="0.001" step={item.product.unit==="UN"?1:0.001} className="w-20 rounded-xl border-stroke bg-white text-center" value={item.quantity} onChange={(e)=>updateQuantity(item.product.id,Number(e.target.value))}/><Button variant="ghost" onClick={()=>updateQuantity(item.product.id,item.quantity+(item.product.unit==="UN"?1:0.1))}><Plus size={15}/></Button></div><input aria-label={`Desconto ${item.product.name}`} type="number" min="0" step="0.01" className="rounded-xl border-stroke bg-white" value={item.discount} onChange={(e)=>setCart(c=>c.map(i=>i.product.id===item.product.id?{...i,discount:Number(e.target.value)}:i))}/><div className="flex items-center justify-between"><b>{formatCurrency(item.product.sale_price*item.quantity-item.discount)}</b><Button variant="ghost" onClick={()=>setCart(c=>c.filter(i=>i.product.id!==item.product.id))}><Trash2 size={16}/></Button></div></div>)}</div>}</Card>
      </>}
    </div>
    <div className="space-y-6">{register&&<Card><p className="text-sm text-slate-500">Total da venda</p><p className="mt-2 text-4xl font-semibold">{formatCurrency(total)}</p><div className="mt-5 grid gap-3"><label className="text-sm">Desconto geral<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={discount} onChange={(e)=>setDiscount(Number(e.target.value))}/></label><label className="text-sm">Acréscimo<input type="number" min="0" step="0.01" className="mt-1 w-full rounded-xl border-stroke bg-white" value={surcharge} onChange={(e)=>setSurcharge(Number(e.target.value))}/></label><label className="text-sm">Observação<input className="mt-1 w-full rounded-xl border-stroke bg-white" value={note} onChange={(e)=>setNote(e.target.value)}/></label></div><Button className="mt-5 w-full" disabled={!cart.length} onClick={()=>{setPayments([{method:"PIX",amount:total}]);setCheckout(true)}}>FINALIZAR VENDA</Button><Button variant="secondary" className="mt-2 w-full" disabled={!cart.length} onClick={()=>void putOnHold()}><Clock3 size={16} className="mr-2"/>Colocar em espera</Button></Card>}
      {register&&<Card><h2 className="font-semibold">Operações do caixa</h2><p className="mt-2 text-sm text-slate-500">Dinheiro esperado: {formatCurrency(register.summary.expected_cash)}</p><div className="mt-4 grid grid-cols-2 gap-2"><Button variant="secondary" onClick={()=>setCashModal("withdrawal")}>Sangria</Button><Button variant="secondary" onClick={()=>setCashModal("supply")}>Suprimento</Button><Button className="col-span-2" onClick={()=>{setCashValue(register.summary.expected_cash);setCashModal("close")}}>Fechar caixa</Button></div></Card>}
      <Card><h2 className="font-semibold">Vendas em espera</h2>{!held.length?<p className="mt-3 text-sm text-slate-500">Nenhuma venda em espera no momento.</p>:held.map(s=><div key={s.id} className="mt-3 flex items-center gap-2 rounded-xl border border-stroke p-2"><button className="flex flex-1 justify-between p-1 text-left" onClick={()=>recover(s)}><span>{s.number}</span><b>{formatCurrency(s.total)}</b></button><Button variant="ghost" aria-label={`Cancelar ${s.number}`} onClick={()=>void cancelHeld(s)}><Trash2 size={16}/></Button></div>)}</Card>
    </div>
    {checkout&&<Modal title="Finalizar venda" onClose={()=>setCheckout(false)}><div className="space-y-4"><p className="text-3xl font-semibold">{formatCurrency(total)}</p>{payments.map((payment,index)=><div key={index} className="grid gap-2 md:grid-cols-3"><select className="rounded-xl border-stroke bg-white" value={payment.method} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,method:e.target.value}:x))}>{["DINHEIRO","PIX","DEBITO","CREDITO"].map(m=><option key={m}>{m}</option>)}</select><input aria-label="Valor do pagamento" type="number" step="0.01" className="rounded-xl border-stroke bg-white" value={payment.amount} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,amount:Number(e.target.value)}:x))}/>{payment.method==="DINHEIRO"?<input aria-label="Valor recebido" type="number" step="0.01" placeholder="Recebido" className="rounded-xl border-stroke bg-white" value={payment.amount_received??payment.amount} onChange={(e)=>setPayments(p=>p.map((x,i)=>i===index?{...x,amount_received:Number(e.target.value)}:x))}/>:<Button variant="ghost" onClick={()=>setPayments(p=>p.filter((_,i)=>i!==index))}>Remover</Button>}</div>)}<Button variant="secondary" onClick={()=>setPayments(p=>[...p,{method:"PIX",amount:Math.max(total-paid,0)}])}>Adicionar pagamento</Button><div className="flex justify-between text-sm"><span>Total informado: {formatCurrency(paid)}</span><span>Troco: {formatCurrency(change)}</span></div>{requiresAuthorization&&<Card className="bg-amber-50"><p className="mb-3 text-sm font-medium text-amber-800">Desconto acima de 10%: informe um gerente ou administrador.</p><div className="grid gap-2 md:grid-cols-2"><input type="email" placeholder="E-mail do autorizador" className="rounded-xl border-stroke bg-white" value={authorizationEmail} onChange={(e)=>setAuthorizationEmail(e.target.value)}/><input type="password" placeholder="Senha do autorizador" className="rounded-xl border-stroke bg-white" value={authorizationPassword} onChange={(e)=>setAuthorizationPassword(e.target.value)}/></div></Card>}{error&&<p className="text-sm text-rose-600">{error}</p>}<Button className="w-full" disabled={processing||Math.abs(paid-total)>0.009||(requiresAuthorization&&(!authorizationEmail||!authorizationPassword))} onClick={()=>void finalize()}>{processing?"Confirmando...":"CONFIRMAR VENDA"}</Button></div></Modal>}
    {cashModal&&<Modal title={cashModal==="open"?"Abrir caixa":cashModal==="close"?"Fechar caixa":cashModal==="withdrawal"?"Sangria":"Suprimento"} onClose={()=>setCashModal(null)}><div className="space-y-4"><label className="block text-sm">{cashModal==="close"?"Valor físico contado":"Valor"}<input type="number" min="0" step="0.01" className="mt-2 w-full rounded-xl border-stroke bg-white" value={cashValue} onChange={(e)=>setCashValue(Number(e.target.value))}/></label>{cashModal!=="open"&&<label className="block text-sm">Motivo/observação<input className="mt-2 w-full rounded-xl border-stroke bg-white" value={cashReason} onChange={(e)=>setCashReason(e.target.value)}/></label>}<Button className="w-full" disabled={processing||(cashModal!=="open"&&!cashReason.trim())} onClick={()=>void submitCashOperation()}>Confirmar</Button></div></Modal>}
    {receipt&&<Modal title={`Comprovante ${receipt.number}`} onClose={()=>setReceipt(null)}><div id="receipt" className="space-y-3"><p className="text-center text-xl font-semibold">Vendi</p>{receipt.items.map(i=><div key={i.id} className="flex justify-between text-sm"><span>{i.quantity}x {i.product_name}</span><span>{formatCurrency(i.subtotal)}</span></div>)}<div className="border-t border-stroke pt-3"><div className="flex justify-between font-semibold"><span>Total</span><span>{formatCurrency(receipt.total)}</span></div><p className="mt-2 text-sm">Pagamento: {receipt.payment_method}</p><p className="text-sm">Troco: {formatCurrency(receipt.change_amount??0)}</p></div><Button className="w-full print:hidden" onClick={()=>window.print()}>Imprimir comprovante</Button></div></Modal>}
  </div>;
}
