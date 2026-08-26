import { Minus, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { Modal } from "../components/Modal";
import { useToast } from "../components/ToastProvider";
import { useHotkeys } from "../hooks/useHotkeys";
import { catalogService } from "../services/catalog";
import { salesService } from "../services/sales";
import type { Product } from "../types";
import { formatCurrency } from "../utils/format";

interface CartItem {
  product: Product;
  quantity: number;
  discount: number;
}

export function CashierPage() {
  const toast = useToast();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [globalDiscount, setGlobalDiscount] = useState(0);
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState("PIX");
  const [amountReceived, setAmountReceived] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    inputRef.current?.focus();
  }, [cart.length]);

  useHotkeys({
    f2: () => inputRef.current?.focus(),
    f4: () => cart.length > 0 && setCheckoutOpen(true),
    escape: () => setCheckoutOpen(false),
    delete: () => {
      if (cart.length > 0) {
        setCart((current) => current.slice(0, -1));
      }
    },
  });

  const subtotal = cart.reduce((sum, item) => sum + item.product.sale_price * item.quantity - item.discount, 0);
  const totalDiscount = cart.reduce((sum, item) => sum + item.discount, 0) + globalDiscount;
  const total = Math.max(subtotal - globalDiscount, 0);
  const change = paymentMethod === "DINHEIRO" ? Math.max(amountReceived - total, 0) : 0;
  const itemsCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  async function addProductByQuery() {
    if (!query.trim()) return;
    setError("");
    try {
      const product = await catalogService.getProductByBarcode(query.trim());
      setCart((current) => {
        const existing = current.find((item) => item.product.id === product.id);
        if (existing) {
          return current.map((item) =>
            item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item,
          );
        }
        return [...current, { product, quantity: 1, discount: 0 }];
      });
      setQuery("");
      toast.push(`${product.name} adicionado ao carrinho.`);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Produto não encontrado.");
    } finally {
      inputRef.current?.focus();
    }
  }

  async function finalizeSale() {
    setProcessing(true);
    setError("");
    try {
      await salesService.create({
        items: cart.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
          discount: item.discount,
        })),
        discount: globalDiscount,
        payment_method: paymentMethod,
        amount_received: paymentMethod === "DINHEIRO" ? amountReceived : undefined,
      });
      toast.push("Venda confirmada com sucesso.");
      setCart([]);
      setGlobalDiscount(0);
      setCheckoutOpen(false);
      setPaymentMethod("PIX");
      setAmountReceived(0);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Não foi possível finalizar a venda.");
    } finally {
      setProcessing(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.6fr_0.8fr]">
      <div className="space-y-6">
        <Card className="overflow-hidden p-0">
          <div className="grid gap-4 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.20),_transparent_30%),linear-gradient(120deg,#09111f_0%,#102032_50%,#101827_100%)] px-6 py-6 md:grid-cols-[1.25fr_0.75fr]">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-emerald-300">Frente de Caixa</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">Venda rápida com foco total em operação.</h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
                Caixa #01 • pronto para leitor USB, atalhos de teclado e fechamento de venda sem perder o foco do operador.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-1">
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Itens no carrinho</p>
                <p className="mt-2 text-2xl font-semibold text-white">{itemsCount}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Descontos</p>
                <p className="mt-2 text-2xl font-semibold text-white">{formatCurrency(totalDiscount)}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Pagamento</p>
                <p className="mt-2 text-2xl font-semibold text-white">{paymentMethod}</p>
              </div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex flex-col gap-3 md:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
              <input
                ref={inputRef}
                className="w-full rounded-2xl border-stroke bg-slate-900/70 py-4 pl-11 pr-4 text-lg text-slate-100"
                placeholder="Código de barras, nome ou SKU"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    void addProductByQuery();
                  }
                }}
              />
            </div>
            <Button className="px-6 py-4" onClick={() => void addProductByQuery()}>
              Adicionar
            </Button>
          </div>
          {error && <p className="mt-3 rounded-xl bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p>}
        </Card>
        <Card>
          <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <h2 className="text-lg font-semibold">Carrinho</h2>
            <div className="flex flex-wrap gap-2 text-xs text-slate-300">
              <span className="rounded-full bg-slate-900 px-3 py-1.5">F2 buscar</span>
              <span className="rounded-full bg-slate-900 px-3 py-1.5">F4 finalizar</span>
              <span className="rounded-full bg-slate-900 px-3 py-1.5">Delete remove último</span>
              <span className="rounded-full bg-slate-900 px-3 py-1.5">ESC fecha modal</span>
            </div>
          </div>
          {cart.length === 0 ? (
            <EmptyState title="Carrinho vazio" description="Escaneie ou pesquise um produto para iniciar a venda." />
          ) : (
            <div className="space-y-3">
              {cart.map((item) => (
                <div key={item.product.id} className="grid gap-3 rounded-2xl border border-stroke/70 bg-slate-900/70 p-4 md:grid-cols-[2fr_repeat(4,1fr)] md:items-center">
                  <div>
                    <p className="font-medium">{item.product.name}</p>
                    <p className="text-xs text-slate-500">{item.product.barcode || item.product.sku}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" onClick={() => setCart((current) => current.map((cartItem) => cartItem.product.id === item.product.id ? { ...cartItem, quantity: Math.max(cartItem.quantity - 1, 1) } : cartItem))}>
                      <Minus size={16} />
                    </Button>
                    <input
                      type="number"
                      min="1"
                      className="w-16 rounded-xl border-stroke bg-slate-950/80 text-center text-slate-100"
                      value={item.quantity}
                      onChange={(event) =>
                        setCart((current) =>
                          current.map((cartItem) =>
                            cartItem.product.id === item.product.id
                              ? { ...cartItem, quantity: Math.max(Number(event.target.value), 1) }
                              : cartItem,
                          ),
                        )
                      }
                    />
                    <Button variant="ghost" onClick={() => setCart((current) => current.map((cartItem) => cartItem.product.id === item.product.id ? { ...cartItem, quantity: cartItem.quantity + 1 } : cartItem))}>
                      <Plus size={16} />
                    </Button>
                  </div>
                  <p>{formatCurrency(item.product.sale_price)}</p>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="rounded-xl border-stroke bg-slate-950/80 text-slate-100"
                    value={item.discount}
                    onChange={(event) =>
                      setCart((current) =>
                        current.map((cartItem) =>
                          cartItem.product.id === item.product.id ? { ...cartItem, discount: Number(event.target.value) } : cartItem,
                        ),
                      )
                    }
                  />
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-emerald-300">
                      {formatCurrency(item.product.sale_price * item.quantity - item.discount)}
                    </span>
                    <Button variant="ghost" onClick={() => setCart((current) => current.filter((cartItem) => cartItem.product.id !== item.product.id))}>
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
      <div className="space-y-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Resumo da venda</p>
              <p className="mt-2 text-4xl font-semibold">{formatCurrency(total)}</p>
            </div>
            <Badge label={cart.length > 0 ? "NORMAL" : "SEM ESTOQUE"} />
          </div>
          <div className="mt-6 grid gap-3 text-sm">
            <div className="flex justify-between text-slate-400">
              <span>Subtotal</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Descontos</span>
              <span>-{formatCurrency(totalDiscount)}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Itens</span>
              <span>{itemsCount}</span>
            </div>
            <label className="block space-y-2">
              <span className="text-slate-400">Desconto geral</span>
              <input
                type="number"
                min="0"
                step="0.01"
                className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
                value={globalDiscount}
                onChange={(event) => setGlobalDiscount(Number(event.target.value))}
              />
            </label>
          </div>
          <Button className="mt-6 w-full py-4 text-base" disabled={cart.length === 0} onClick={() => setCheckoutOpen(true)}>
            FINALIZAR VENDA
          </Button>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold">Dicas operacionais</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-300">
            <li>Leitores USB funcionam como teclado: escaneie e pressione Enter.</li>
            <li>O campo principal volta a receber foco após cada inclusão.</li>
            <li>Se o produto não existir, o sistema mostra o erro e permite cadastrar pela tela de produtos.</li>
          </ul>
        </Card>
      </div>

      {checkoutOpen && (
        <Modal title="Finalizar venda" onClose={() => setCheckoutOpen(false)}>
          <div className="space-y-5">
            <Card className="bg-slate-900/70">
              <p className="text-sm text-slate-400">TOTAL DA VENDA</p>
              <p className="mt-2 text-4xl font-semibold">{formatCurrency(total)}</p>
            </Card>
            <div className="grid gap-4 md:grid-cols-2">
              {["PIX", "DINHEIRO", "DEBITO", "CREDITO"].map((method) => (
                <button
                  key={method}
                  className={`rounded-2xl border px-4 py-4 text-left transition ${
                    paymentMethod === method
                      ? "border-brand bg-brand/15 text-white"
                      : "border-stroke bg-slate-900/60 text-slate-300"
                  }`}
                  onClick={() => setPaymentMethod(method)}
                >
                  {method}
                </button>
              ))}
            </div>
            {paymentMethod === "DINHEIRO" && (
              <div className="grid gap-4 md:grid-cols-2">
                <label className="space-y-2 text-sm">
                  <span>Valor recebido</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
                    value={amountReceived}
                    onChange={(event) => setAmountReceived(Number(event.target.value))}
                  />
                </label>
                <Card className="bg-slate-900/70">
                  <p className="text-sm text-slate-400">Troco</p>
                  <p className="mt-2 text-2xl font-semibold text-emerald-300">{formatCurrency(change)}</p>
                </Card>
              </div>
            )}
            {error && <p className="rounded-xl bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p>}
            <Button className="w-full py-4 text-base" onClick={() => void finalizeSale()} disabled={processing}>
              {processing ? "Confirmando..." : "CONFIRMAR VENDA"}
            </Button>
          </div>
        </Modal>
      )}
    </div>
  );
}
