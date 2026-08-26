import { Card } from "../components/Card";

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Configurações</h1>
        <p className="page-subtitle">Espaço preparado para futuras preferências operacionais e regras de negócio.</p>
      </div>
      <Card>
        <h2 className="text-lg font-semibold">Próximas evoluções</h2>
        <ul className="mt-4 space-y-3 text-sm text-slate-300">
          <li>Configuração de múltiplos caixas e múltiplas lojas.</li>
          <li>Regras para NFC-e e integrações fiscais em versões futuras.</li>
          <li>Parâmetros de alertas, horário comercial e formas de pagamento.</li>
        </ul>
      </Card>
    </div>
  );
}
