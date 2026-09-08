import clsx from "clsx";
import { classByStatus } from "../utils/format";

export function Badge({ label, className }: { label: string; className?: string }) {
  return <span className={clsx("rounded-full px-2.5 py-1 text-xs font-semibold", classByStatus[label] ?? "bg-brandDeeper/10 text-brandDeeper", className)}>{label}</span>;
}
