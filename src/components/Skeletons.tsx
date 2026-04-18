export function HeroSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="h-12 w-4/5 rounded-full bg-white/10" />
      <div className="h-6 w-2/3 rounded-full bg-white/10" />
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="h-28 rounded-3xl bg-white/10" />
        ))}
      </div>
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="animate-pulse rounded-3xl border border-white/10 bg-panel p-5 shadow-card">
      <div className="h-6 w-3/4 rounded-full bg-white/10" />
      <div className="mt-4 h-4 w-2/5 rounded-full bg-white/10" />
      <div className="mt-6 space-y-2">
        <div className="h-4 rounded-full bg-white/10" />
        <div className="h-4 rounded-full bg-white/10" />
        <div className="h-4 w-4/5 rounded-full bg-white/10" />
      </div>
    </div>
  );
}
