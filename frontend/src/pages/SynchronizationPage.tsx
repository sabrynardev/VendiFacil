import { AlertTriangle, CheckCircle2, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { useConnectivity } from "../contexts/ConnectivityContext";
import { useAuth } from "../contexts/AuthContext";
import { allOperations, queueOperation, type QueueOperation } from "../services/offlineDb";
import { syncService, type ServerSyncLog } from "../services/synchronization";
import { formatDateTime } from "../utils/format";

export function SynchronizationPage() {
  const connectivity = useConnectivity();
  const { user } = useAuth();
  const [local, setLocal] = useState<QueueOperation[]>([]);
  const [logs, setLogs] = useState<ServerSyncLog[]>([]);

  async function load() {
    setLocal((await allOperations()).filter(item => item.account_id === user?.account_id && item.user_id === user?.id));
    try { setLogs(await syncService.logs()); } catch { setLogs([]); }
  }
  useEffect(() => { void load(); }, [connectivity.status, connectivity.pending, connectivity.attention, user?.id]);
  async function retry(item: QueueOperation) { await queueOperation({ ...item, status: "PENDING", error: undefined, next_attempt_at: undefined }); await connectivity.checkNow(); await load(); }

  return <div className="space-y-6"><div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><h1 className="page-title">Sincronização</h1><p className="page-subtitle">Suas vendas offline permanecem guardadas até o servidor confirmar o recebimento.</p></div><Button variant="secondary" onClick={() => void connectivity.checkNow()} disabled={connectivity.status === "SYNCING"}><RefreshCw size={16} className={`mr-2 ${connectivity.status === "SYNCING" ? "animate-spin" : ""}`}/>Sincronizar agora</Button></div>
    <div className="grid gap-4 md:grid-cols-3"><Card><p className="text-sm text-slate-500">Conexão</p><p className="mt-2 text-2xl font-semibold">{connectivity.status.replace("SYNC_ERROR", "COM PENDÊNCIAS")}</p></Card><Card><p className="text-sm text-slate-500">Aguardando</p><p className="mt-2 text-2xl font-semibold">{connectivity.pending}</p></Card><Card><p className="text-sm text-slate-500">Requer atenção</p><p className="mt-2 text-2xl font-semibold text-amber-700">{connectivity.attention}</p></Card></div>
    <Card><h2 className="font-semibold">Neste dispositivo</h2>{!local.length ? <EmptyState title="Tudo sincronizado" description="Nenhuma operação local está aguardando envio."/> : <div className="mt-4 space-y-3">{local.map(item => <div key={item.operation_id} className="flex flex-col justify-between gap-3 rounded-2xl border border-stroke p-4 md:flex-row md:items-center"><div><div className="flex items-center gap-2"><Badge label={item.status}/><span className="text-sm font-medium">Venda offline</span></div><p className="mt-2 text-xs text-slate-500">{item.payload.device_id} · {formatDateTime(item.created_at)} · {item.attempts} tentativa(s)</p>{item.error && <p className="mt-2 text-sm text-amber-700">{item.error}</p>}</div>{item.status === "ATTENTION" && <Button variant="secondary" onClick={() => void retry(item)}>Tentar novamente</Button>}</div>)}</div>}</Card>
    <Card><h2 className="font-semibold">Confirmações do servidor</h2>{!logs.length ? <EmptyState title="Sem histórico disponível" description="As confirmações aparecerão quando houver sincronizações."/> : <div className="mt-4 space-y-3">{logs.slice(0, 20).map(item => <div key={item.operation_id} className="flex items-start gap-3 rounded-2xl bg-brand/4 p-4">{item.conflict ? <AlertTriangle className="text-amber-600" size={18}/> : <CheckCircle2 className="text-emerald-600" size={18}/>}<div><p className="text-sm font-medium">{item.status.replace(/_/g, " ")}</p><p className="mt-1 text-xs text-slate-500">{item.device_id} · {formatDateTime(item.updated_at)} · {item.duration_ms} ms</p>{item.error_message && <p className="mt-2 text-sm text-amber-700">{item.error_message}</p>}</div></div>)}</div>}</Card>
  </div>;
}
