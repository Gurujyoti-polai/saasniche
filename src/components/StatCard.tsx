type StatCardProps = {
  label: string;
  value: string;
  accent?: boolean;
};

export function StatCard({ label, value, accent = false }: StatCardProps) {
  return (
    <div
      className={`rounded-3xl border px-5 py-6 shadow-card ${
        accent
          ? "border-accent/40 bg-gradient-to-br from-accent/20 to-panel"
          : "border-white/10 bg-panel"
      }`}
    >
      <p className="text-sm uppercase tracking-[0.24em] text-muted">{label}</p>
      <p className="mt-3 text-3xl font-extrabold text-white">{value}</p>
    </div>
  );
}
