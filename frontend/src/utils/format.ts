export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value ?? 0);

export const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));

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
};
