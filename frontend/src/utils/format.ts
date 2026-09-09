export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value ?? 0);

export const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));

export const formatDate = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "UTC" }).format(new Date(`${value}T00:00:00Z`));

export const classByStatus: Record<string, string> = {
  NORMAL: "bg-brand/10 text-brandStrong",
  BAIXO: "bg-amber-100 text-amber-700",
  "CRÍTICO": "bg-rose-100 text-rose-700",
  "SEM ESTOQUE": "bg-rose-200 text-rose-800",
  OPEN: "bg-emerald-100 text-emerald-700",
  CLOSED: "bg-slate-100 text-slate-700",
  COMPLETED: "bg-emerald-100 text-emerald-700",
  ON_HOLD: "bg-amber-100 text-amber-700",
  CANCELLED: "bg-rose-100 text-rose-700",
  RASCUNHO: "bg-slate-100 text-slate-700",
  ENVIADO: "bg-blue-100 text-blue-700",
  AGUARDANDO: "bg-amber-100 text-amber-700",
  PARCIALMENTE_RECEBIDO: "bg-amber-100 text-amber-700",
  RECEBIDO: "bg-emerald-100 text-emerald-700",
  CANCELADO: "bg-rose-100 text-rose-700",
  VENCIDO: "bg-rose-100 text-rose-700",
  VENCE_HOJE: "bg-rose-100 text-rose-700",
  ATE_3_DIAS: "bg-amber-100 text-amber-700",
  ATE_7_DIAS: "bg-amber-100 text-amber-700",
  ATE_30_DIAS: "bg-blue-100 text-blue-700",
  SEM_VALIDADE: "bg-slate-100 text-slate-700",
  EM_ANDAMENTO: "bg-amber-100 text-amber-700",
  CONCLUIDO: "bg-emerald-100 text-emerald-700",
  EM_ABERTO: "bg-amber-100 text-amber-700",
  PARCIAL: "bg-blue-100 text-blue-700",
  QUITADO: "bg-emerald-100 text-emerald-700",
  ESTORNADO: "bg-slate-100 text-slate-700",
  PENDENTE: "bg-amber-100 text-amber-700",
  PAGA: "bg-emerald-100 text-emerald-700",
  VENCIDA: "bg-rose-100 text-rose-700",
  BLOQUEADO: "bg-rose-100 text-rose-700",
  LIBERADO: "bg-emerald-100 text-emerald-700",
};
