import type { ReactNode } from "react";

export function DataTable({
  headers,
  children,
}: {
  headers: string[];
  children: ReactNode;
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-stroke">
      <table className="min-w-full divide-y divide-stroke text-sm">
        <thead className="bg-slate-900/70 text-left text-slate-400">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-stroke bg-surface/60">{children}</tbody>
      </table>
    </div>
  );
}
