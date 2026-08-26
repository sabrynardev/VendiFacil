import clsx from "clsx";
import type { PropsWithChildren } from "react";

export function Card({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <div className={clsx("glass-panel rounded-2xl p-5", className)}>{children}</div>;
}
