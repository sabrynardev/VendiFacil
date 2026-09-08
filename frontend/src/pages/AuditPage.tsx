import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { useAsync } from "../hooks/useAsync";
import { administrationService } from "../services/administration";
import { formatDateTime } from "../utils/format";

const actionLabel: Record<string, string> = {
  CREATE: "Criação",
  UPDATE: "Alteração",
  DELETE: "Exclusão",
  ARCHIVE: "Arquivamento",
  STOCK_MOVEMENT: "Estoque",
};

export function AuditPage() {
  const { data, loading, error } = useAsync(() => administrationService.listAudit(), []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Auditoria</h1>
        <p className="page-subtitle">Histórico de operações sensíveis realizadas no estabelecimento.</p>
      </div>
      <Card>
        {loading ? <p className="text-sm text-slate-500">Carregando histórico...</p> : error ? (
          <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>
        ) : !data?.length ? (
          <EmptyState title="Nenhuma operação registrada" description="As próximas alterações importantes aparecerão aqui." />
        ) : (
          <DataTable headers={["Data e hora", "Usuário", "Operação", "Registro", "Descrição"]}>
            {data.map((entry) => (
              <tr key={entry.id}>
                <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDateTime(entry.created_at)}</td>
                <td className="px-4 py-3 font-medium">{entry.user_name || "Sistema"}</td>
                <td className="px-4 py-3">{actionLabel[entry.action] || entry.action}</td>
                <td className="px-4 py-3 text-slate-600">{entry.entity_type} {entry.entity_id ? `#${entry.entity_id}` : ""}</td>
                <td className="px-4 py-3 text-slate-600">{entry.description}</td>
              </tr>
            ))}
          </DataTable>
        )}
      </Card>
    </div>
  );
}
