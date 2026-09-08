import clsx from "clsx";
import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}

export function Button({ children, className, variant = "primary", ...props }: PropsWithChildren<Props>) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-medium transition duration-200",
        variant === "primary" && "bg-brand text-white shadow-[0_14px_32px_rgba(2,59,230,0.22)] hover:bg-brandStrong",
        variant === "secondary" && "border border-brand/20 bg-brand/5 text-brandDark hover:bg-brand/10",
        variant === "ghost" && "bg-transparent text-brandDark hover:bg-brand/6",
        variant === "danger" && "bg-danger text-white hover:bg-rose-600",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
