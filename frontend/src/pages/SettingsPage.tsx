import { Card } from "../components/Card";
import { useAuth } from "../contexts/AuthContext";

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Configurações</h1>
        <p className="page-subtitle">Ambiente da conta, preferências futuras e base comercial isolada por cliente.</p>
      </div>

      <Card>
        <h2 className="text-lg font-semibold">Conta ativa</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-stroke bg-brand/4 p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Conta</p>
            <p className="mt-2 text-lg font-semibold text-brandDeeper">{user?.account.name}</p>
          </div>
          <div className="rounded-2xl border border-stroke bg-brand/4 p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Administrador atual</p>
            <p className="mt-2 text-lg font-semibold text-brandDeeper">{user?.name}</p>
          </div>
          <div className="rounded-2xl border border-stroke bg-brand/4 p-4">
            <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Status</p>
            <p className="mt-2 text-lg font-semibold text-brandDeeper">{user?.account.active ? "Ativa" : "Inativa"}</p>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold">Próximas evoluções</h2>
        <ul className="mt-4 space-y-3 text-sm text-slate-600">
          <li>Múltiplos usuários por conta com permissões separadas.</li>
          <li>Parâmetros fiscais, caixas e preferências por cliente.</li>
          <li>Onboarding guiado para primeiro cadastro de produtos e estoque.</li>
        </ul>
      </Card>
    </div>
  );
}
