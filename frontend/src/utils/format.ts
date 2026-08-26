export const formatCurrency = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value ?? 0);

export const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));

export const classByStatus: Record<string, string> = {
  NORMAL: "bg-emerald-500/15 text-emerald-300",
  BAIXO: "bg-amber-500/15 text-amber-300",
  "CRÍTICO": "bg-rose-500/15 text-rose-300",
  "SEM ESTOQUE": "bg-rose-600/20 text-rose-200",
};
