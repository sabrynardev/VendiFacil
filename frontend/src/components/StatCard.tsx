import { TrendingDown, TrendingUp } from "lucide-react";
import { Card } from "./Card";
import { formatCurrency } from "../utils/format";

export function StatCard({
  title,
  value,
  delta,
  currency,
}: {
  title: string;
  value: number;
  delta?: number;
  currency?: boolean;
}) {
  const positive = (delta ?? 0) >= 0;

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-brandDeeper">{currency ? formatCurrency(value) : value}</p>
        </div>
        <div className={`rounded-2xl p-2 ${positive ? "bg-brand/10 text-brand" : "bg-danger/10 text-danger"}`}>
          {positive ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
        </div>
      </div>
      {delta !== undefined && (
        <p className={`mt-4 text-sm ${positive ? "text-brandStrong" : "text-danger"}`}>
          {currency ? formatCurrency(Math.abs(delta)) : Math.abs(delta)} em relação a ontem
        </p>
      )}
    </Card>
  );
}
