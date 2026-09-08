import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { brand } from "../config/brand";
import { fetchMe, registerAccount } from "../services/auth";

export function RegisterPage() {
  const navigate = useNavigate();
  const [accountName, setAccountName] = useState("");
  const [adminName, setAdminName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [password, setPassword] = useState("");
  const [withDefaultCategories, setWithDefaultCategories] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { access_token } = await registerAccount({
        account_name: accountName,
        admin_name: adminName,
        admin_email: adminEmail,
        password,
        with_default_categories: withDefaultCategories,
      });
      localStorage.setItem("vendifacil:token", access_token);
      await fetchMe();
      navigate("/");
      window.location.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível criar a conta.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <Card className="w-full max-w-4xl overflow-hidden border-brand/10 p-0">
        <div className="grid lg:grid-cols-[0.95fr_1.05fr]">
          <div className="bg-[radial-gradient(circle_at_top_left,_rgba(2,59,230,0.12),_transparent_30%),linear-gradient(180deg,#ffffff_0%,#eef4ff_100%)] p-8 md:p-10">
            <div className="inline-flex rounded-full border border-brand/10 bg-brand/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.28em] text-brand">
              {brand.shortName}
            </div>
            <h1 className="mt-4 text-4xl font-semibold leading-tight text-brandDeeper">Crie uma nova conta pronta para uso.</h1>
            <p className="mt-4 text-slate-600">
              Cada conta nasce separada das demais, com ambiente próprio, sem produtos, sem vendas e com categorias iniciais para começar mais rápido.
            </p>
            <div className="mt-8 space-y-3 text-sm text-slate-600">
              <p>Conta nova com dados isolados.</p>
              <p>Admin próprio para o cliente.</p>
              <p>Base limpa e pronta para cadastrar estoque.</p>
            </div>
          </div>

          <div className="p-8 md:p-10">
            <h2 className="text-2xl font-semibold text-brandDeeper">Criar conta</h2>
            <p className="mt-2 text-sm text-slate-500">Abra um novo ambiente comercial sem misturar dados com a demo.</p>
            <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
              <label className="block space-y-2 text-sm">
                <span>Nome da conta / empresa</span>
                <input required minLength={2} className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={accountName} onChange={(event) => setAccountName(event.target.value)} />
              </label>
              <label className="block space-y-2 text-sm">
                <span>Nome do administrador</span>
                <input required minLength={2} className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={adminName} onChange={(event) => setAdminName(event.target.value)} />
              </label>
              <label className="block space-y-2 text-sm">
                <span>E-mail do administrador</span>
                <input required type="email" className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={adminEmail} onChange={(event) => setAdminEmail(event.target.value)} />
              </label>
              <label className="block space-y-2 text-sm">
                <span>Senha</span>
                <input required minLength={6} type="password" className="w-full rounded-xl border-stroke bg-white text-brandDeeper" value={password} onChange={(event) => setPassword(event.target.value)} />
              </label>
              <label className="flex items-center gap-3 rounded-2xl border border-stroke bg-brand/4 px-4 py-3 text-sm text-slate-600">
                <input type="checkbox" checked={withDefaultCategories} onChange={(event) => setWithDefaultCategories(event.target.checked)} />
                Criar categorias iniciais para começar mais rápido
              </label>
              {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
              <Button className="w-full py-3" type="submit" disabled={loading}>
                {loading ? "Criando conta..." : "Criar conta nova"}
              </Button>
            </form>

            <div className="mt-6 text-sm text-slate-500">
              <Link className="text-brand hover:text-brandStrong" to="/login">
                Voltar para o login
              </Link>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
