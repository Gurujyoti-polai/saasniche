import { useEffect } from "react";

import type { IdeaDetail } from "../types";

type IdeaDetailModalProps = {
  idea: IdeaDetail | null;
  loading: boolean;
  onClose: () => void;
};

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
      <p className="text-xs uppercase tracking-[0.18em] text-muted">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

export function IdeaDetailModal({
  idea,
  loading,
  onClose,
}: IdeaDetailModalProps) {
  useEffect(() => {
    function onEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", onEscape);
    return () => window.removeEventListener("keydown", onEscape);
  }, [onClose]);

  if (!idea && !loading) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 py-8 backdrop-blur-sm">
      <div className="relative max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-[2rem] border border-white/10 bg-ink p-6 shadow-card md:p-8">
        <button
          className="absolute right-5 top-5 rounded-full border border-white/10 px-3 py-2 text-sm text-white transition hover:border-accent hover:text-accent"
          onClick={onClose}
          type="button"
        >
          X
        </button>

        {loading || !idea ? (
          <div className="animate-pulse space-y-4 pt-8">
            <div className="h-8 w-4/5 rounded-full bg-white/10" />
            <div className="h-5 w-1/2 rounded-full bg-white/10" />
            <div className="h-28 rounded-3xl bg-white/10" />
          </div>
        ) : (
          <div className="space-y-8 pt-8">
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-accent">
                  {idea.category}
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-200">
                  {idea.profession}
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1 text-sm text-white">
                  Score {idea.score.toFixed(1)}
                </span>
              </div>
              <h2 className="text-3xl font-extrabold text-white">{idea.title}</h2>
              <a
                className="text-blue-400 transition hover:underline"
                href={idea.url}
                rel="noreferrer"
                target="_blank"
              >
                View on Reddit ↗
              </a>
              {idea.created_at ? (
                <p className="text-sm text-gray-400">
                  Posted: {new Date(idea.created_at).toLocaleDateString()}
                </p>
              ) : null}
            </div>

            <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <section className="space-y-6">
                <div>
                  <p className="text-sm uppercase tracking-[0.22em] text-muted">
                    Problem Summary
                  </p>
                  <p className="mt-3 text-base leading-7 text-slate-100">
                    {idea.blueprint.problem_summary}
                  </p>
                </div>
                <div>
                  <p className="text-sm uppercase tracking-[0.22em] text-muted">
                    Solution
                  </p>
                  <p className="mt-3 text-base leading-7 text-slate-100">
                    {idea.blueprint.solution}
                  </p>
                </div>
                <div>
                  <p className="text-sm uppercase tracking-[0.22em] text-muted">
                    Revenue & Pricing
                  </p>
                  <ul className="mt-3 space-y-3 text-slate-100">
                    <li className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                      <span className="block text-xs uppercase tracking-[0.18em] text-muted">
                        Revenue model
                      </span>
                      <span className="mt-2 block text-base font-semibold capitalize">
                        {idea.blueprint.revenue_model.replace("_", " ")}
                      </span>
                    </li>
                    <li className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                      <span className="block text-xs uppercase tracking-[0.18em] text-muted">
                        Pricing
                      </span>
                      <span className="mt-2 block text-base font-semibold">
                        {idea.blueprint.pricing}
                      </span>
                    </li>
                  </ul>
                </div>
                <div>
                  <p className="text-sm uppercase tracking-[0.22em] text-muted">
                    MVP Features
                  </p>
                  <ul className="mt-3 list-disc space-y-2 pl-6 text-slate-100">
                    {idea.blueprint.mvp_features.map((feature) => (
                      <li key={feature}>{feature}</li>
                    ))}
                  </ul>
                </div>
              </section>

              <aside className="space-y-4">
                <DetailRow
                  label="Tech Complexity"
                  value={idea.blueprint.tech_complexity}
                />
                <DetailRow label="Market Size" value={idea.blueprint.market_size} />
                <DetailRow
                  label="Competition"
                  value={idea.blueprint.competition}
                />
                <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">
                    Landing Copy
                  </p>
                  <p className="mt-3 text-base italic text-white">
                    “{idea.blueprint.landing_copy}”
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted">
                    Target Audience
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-100">
                    {idea.blueprint.target_audience}
                  </p>
                </div>
              </aside>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
