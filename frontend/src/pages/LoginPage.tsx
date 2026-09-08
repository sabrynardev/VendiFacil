import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { brand } from "../config/brand";
import { useAuth } from "../contexts/AuthContext";

const highlightItems = [
  { title: "Faturamento", description: "Visão diária do negócio." },
  { title: "Caixa", description: "Venda rápida e organizada." },
  { title: "Estoque", description: "Previsão e alertas automáticos." },
];

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
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <Card className="w-full max-w-5xl overflow-hidden border-brand/10 p-0">
        <div className="grid lg:grid-cols-[1.1fr_0.9fr]">
          <div className="bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_30%),linear-gradient(180deg,#ffffff_0%,#eef4ff_100%)] p-8 md:p-10">
            <div className="inline-flex rounded-full border border-brand/10 bg-brand/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-brand">
              {brand.shortName}
            </div>
            <h1 className="mt-4 text-4xl font-semibold leading-tight text-brandDeeper md:text-5xl">PDV profissional com caixa, estoque e visão gerencial.</h1>
            <p className="mt-4 max-w-xl text-slate-600">
              Controle vendas, acompanhe alertas de estoque e acompanhe a operação do mercadinho com um fluxo rápido para o caixa.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              {highlightItems.map((item) => (
                <div key={item.title} className="rounded-2xl border border-stroke bg-white/80 px-4 py-4 shadow-[0_16px_35px_rgba(2,37,143,0.06)]">
                  <p className="text-sm font-semibold text-brandDeeper">{item.title}</p>
                  <p className="mt-2 text-sm text-slate-500">{item.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-8 md:p-10">
            <h2 className="text-2xl font-semibold text-brandDeeper">Entrar</h2>
            <p className="mt-2 text-sm text-slate-500">Acesse a demonstração ou abra a apresentação comercial.</p>
            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <label className="block space-y-2 text-sm">
                <span>E-mail</span>
                <input
                  type="email"
                  className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
              <label className="block space-y-2 text-sm">
                <span>Senha</span>
                <input
                  type="password"
                  className="w-full rounded-xl border-stroke bg-white text-brandDeeper"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
              <Button className="w-full py-3" type="submit" disabled={loading}>
                {loading ? "Entrando..." : "Entrar"}
              </Button>
            </form>
            <div className="mt-6 rounded-2xl border border-stroke bg-brand/4 p-4 text-sm text-slate-500">
              <p className="leading-6">Quer apresentar a solução antes do login?</p>
              <a className="mt-3 inline-flex text-brand hover:text-brandStrong" href="/apresentacao">
                Ver página de apresentação comercial
              </a>
              <div className="mt-3">
                <Link className="inline-flex text-brand hover:text-brandStrong" to="/registro">
                  Criar uma conta nova zerada
                </Link>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
