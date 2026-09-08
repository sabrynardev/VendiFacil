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
        <thead className="bg-brandDeeper text-left text-blue-100">
          <tr>
            {headers.map((header) => (
              <th key={header} className="px-4 py-3 font-medium">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-stroke bg-white/90 text-brandDeeper">{children}</tbody>
      </table>
    </div>
  );
}
