import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../contexts/AuthContext";

export function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@marketpulse.dev");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await signIn(email, password);
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Não foi possível entrar.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="grid max-w-5xl gap-8 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[2rem] border border-stroke bg-slate-950/50 p-8 shadow-soft backdrop-blur">
          <p className="text-sm uppercase tracking-[0.35em] text-brand">VendiFácil</p>
          <h1 className="mt-4 text-5xl font-semibold leading-tight">PDV profissional com caixa, estoque e visão gerencial.</h1>
          <p className="mt-4 max-w-xl text-slate-400">
            Controle vendas, acompanhe alertas de estoque e acompanhe a operação do mercadinho com um fluxo rápido para o caixa.
          </p>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              ["Faturamento", "Painel com visão diária, ticket médio e histórico recente."],
              ["Caixa", "Busca por SKU, nome ou código de barras com atalhos."],
              ["Estoque", "Previsão de ruptura e recomendação de compra."],
            ].map(([title, description]) => (
              <Card key={title} className="bg-slate-900/80">
                <h3 className="font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-400">{description}</p>
              </Card>
            ))}
          </div>
        </div>
        <Card className="self-center p-8">
          <h2 className="text-2xl font-semibold">Entrar</h2>
          <p className="mt-2 text-sm text-slate-400">Use o usuário padrão para explorar o fluxo de demonstração.</p>
          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block space-y-2 text-sm">
              <span>E-mail</span>
              <input
                type="email"
                className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="block space-y-2 text-sm">
              <span>Senha</span>
              <input
                type="password"
                className="w-full rounded-xl border-stroke bg-slate-900/70 text-slate-100"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            {error && <p className="rounded-xl bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</p>}
            <Button className="w-full py-3" type="submit" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
          <div className="mt-6 rounded-2xl border border-stroke bg-slate-900/60 p-4 text-sm text-slate-400">
            <p>Admin: `admin@marketpulse.dev` / `admin123`</p>
            <p className="mt-1">Operador: `sabrina@marketpulse.dev` / `caixa123`</p>
          </div>
        </Card>
      </div>
    </div>
  );
}
