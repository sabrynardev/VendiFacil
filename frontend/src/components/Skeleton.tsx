export function Skeleton({ className = "h-32 w-full" }: { className?: string }) {
  return <div className={`animate-pulse rounded-2xl bg-brand/10 ${className}`} />;
}
