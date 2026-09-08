export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-stroke bg-brand/5 px-6 py-12 text-center">
      <h3 className="text-lg font-semibold text-brandDeeper">{title}</h3>
      <p className="mt-2 text-sm text-slate-500">{description}</p>
    </div>
  );
}
