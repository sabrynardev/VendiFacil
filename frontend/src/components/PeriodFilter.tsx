import { useState } from "react";

export type PeriodKey = "today" | "yesterday" | "7d" | "30d" | "month" | "previous_month" | "year" | "custom";

const toIso = (value: Date) => value.toISOString().slice(0, 10);

export function periodDates(period: PeriodKey): [string, string] {
  const now = new Date(); const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (period === "today") return [toIso(today), toIso(today)];
  if (period === "yesterday") { const day = new Date(today); day.setDate(day.getDate() - 1); return [toIso(day), toIso(day)]; }
  if (period === "7d" || period === "30d") { const start = new Date(today); start.setDate(start.getDate() - (period === "7d" ? 6 : 29)); return [toIso(start), toIso(today)]; }
  if (period === "month") return [toIso(new Date(today.getFullYear(), today.getMonth(), 1)), toIso(today)];
  if (period === "previous_month") return [toIso(new Date(today.getFullYear(), today.getMonth() - 1, 1)), toIso(new Date(today.getFullYear(), today.getMonth(), 0))];
  if (period === "year") return [toIso(new Date(today.getFullYear(), 0, 1)), toIso(today)];
  return [toIso(today), toIso(today)];
}

const options: Array<[PeriodKey, string]> = [["today", "Hoje"], ["yesterday", "Ontem"], ["7d", "Últimos 7 dias"], ["30d", "Últimos 30 dias"], ["month", "Este mês"], ["previous_month", "Mês anterior"], ["year", "Este ano"], ["custom", "Personalizado"]];

export function PeriodFilter({ start, end, onChange }: { start: string; end: string; onChange: (start: string, end: string) => void }) {
  const [period, setPeriod] = useState<PeriodKey>("30d");
  return <div className="flex flex-wrap items-end gap-3"><label className="text-sm">Período<select className="mt-1 w-full rounded-xl border-stroke bg-white" value={period} onChange={(event) => { const selected = event.target.value as PeriodKey; setPeriod(selected); if (selected !== "custom") onChange(...periodDates(selected)); }}><option value="" disabled>Selecione</option>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>{period === "custom" && <><label className="text-sm">De<input type="date" className="mt-1 w-full rounded-xl border-stroke bg-white" value={start} onChange={(event) => onChange(event.target.value, end)}/></label><label className="text-sm">Até<input type="date" className="mt-1 w-full rounded-xl border-stroke bg-white" value={end} onChange={(event) => onChange(start, event.target.value)}/></label></>}</div>;
}
