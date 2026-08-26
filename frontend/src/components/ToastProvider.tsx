import { createContext, useContext, useMemo, useState, type PropsWithChildren } from "react";

interface Toast {
  id: number;
  title: string;
  tone: "success" | "error";
}

const ToastContext = createContext<{ push: (title: string, tone?: Toast["tone"]) => void } | null>(null);

export function ToastProvider({ children }: PropsWithChildren) {
  const [items, setItems] = useState<Toast[]>([]);

  const value = useMemo(
    () => ({
      push: (title: string, tone: Toast["tone"] = "success") => {
        const toast = { id: Date.now(), title, tone };
        setItems((current) => [...current, toast]);
        window.setTimeout(() => {
          setItems((current) => current.filter((item) => item.id !== toast.id));
        }, 2600);
      },
    }),
    [],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-4 right-4 z-[60] space-y-3">
        {items.map((item) => (
          <div key={item.id} className={`rounded-2xl border px-4 py-3 text-sm shadow-soft ${item.tone === "success" ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100" : "border-rose-500/30 bg-rose-500/10 text-rose-100"}`}>
            {item.title}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast precisa estar dentro de ToastProvider");
  }
  return context;
}
