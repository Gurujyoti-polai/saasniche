import { useEffect, useRef, useState } from "react";

import type { IdeaSummary } from "../types";

type IdeaCardProps = {
  idea: IdeaSummary;
  onView: (idea: IdeaSummary) => void;
};

function scoreClasses(score: number) {
  if (score >= 75) {
    return "bg-emerald-500/20 text-emerald-300 border-emerald-400/30";
  }
  if (score >= 50) {
    return "bg-yellow-500/20 text-yellow-300 border-yellow-400/30";
  }
  return "bg-orange-500/20 text-orange-200 border-orange-400/30";
}

export function IdeaCard({ idea, onView }: IdeaCardProps) {
  const [visible, setVisible] = useState(false);
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "140px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const summary = idea.blueprint.problem_summary;
  const truncatedSummary =
    summary.length > 100 ? `${summary.slice(0, 100).trim()}...` : summary;
  const createdAt = idea.blueprint.created_at || idea.created_at;

  return (
    <article
      ref={ref}
      className="min-h-[16rem] rounded-3xl border border-white/10 bg-panel p-5 shadow-card transition hover:-translate-y-1"
    >
      {!visible ? (
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-4/5 rounded-full bg-white/10" />
          <div className="flex gap-2">
            <div className="h-8 w-20 rounded-full bg-white/10" />
            <div className="h-8 w-24 rounded-full bg-white/10" />
          </div>
          <div className="space-y-2">
            <div className="h-4 rounded-full bg-white/10" />
            <div className="h-4 rounded-full bg-white/10" />
            <div className="h-4 w-3/4 rounded-full bg-white/10" />
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <button
                className="text-left text-lg font-extrabold leading-snug text-white transition hover:text-accent"
                onClick={() => onView(idea)}
                type="button"
              >
                {idea.title}
              </button>
              {createdAt ? (
                <p className="mt-1 text-xs text-gray-400">
                  {new Date(createdAt).toLocaleDateString()}
                </p>
              ) : null}
            </div>
            <div className="flex shrink-0 flex-col items-end gap-2">
              <span
                className={`rounded-full border px-3 py-1 text-sm font-semibold ${scoreClasses(
                  idea.score,
                )}`}
              >
                {idea.score.toFixed(1)}
              </span>
              <a
                className="text-sm text-orange-500 transition hover:text-orange-400"
                href={idea.url}
                rel="noopener noreferrer"
                target="_blank"
              >
                🔗 View on Reddit
              </a>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-accent">
              {idea.category}
            </span>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-slate-200">
              {idea.profession}
            </span>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-200">
            {truncatedSummary}
          </p>
          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              className="rounded-full bg-white px-4 py-2 text-sm font-bold text-ink transition hover:bg-accent hover:text-white"
              onClick={() => onView(idea)}
              type="button"
            >
              View Blueprint
            </button>
          </div>
        </>
      )}
    </article>
  );
}
