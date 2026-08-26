import clsx from "clsx";
import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}

export function Button({ children, className, variant = "primary", ...props }: PropsWithChildren<Props>) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition",
        variant === "primary" && "bg-brand text-white hover:bg-blue-500",
        variant === "secondary" && "bg-surfaceAlt text-slate-100 hover:bg-slate-700",
        variant === "ghost" && "bg-transparent text-slate-300 hover:bg-slate-800/70",
        variant === "danger" && "bg-danger text-white hover:bg-rose-500",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
