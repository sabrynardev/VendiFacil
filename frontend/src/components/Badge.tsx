import clsx from "clsx";
import { classByStatus } from "../utils/format";

export function Badge({ label, className }: { label: string; className?: string }) {
  return <span className={clsx("rounded-full px-2.5 py-1 text-xs font-semibold", classByStatus[label] ?? "bg-slate-700 text-slate-200", className)}>{label}</span>;
}
