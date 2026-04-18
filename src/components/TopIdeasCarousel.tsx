import { useRef } from "react";

import type { IdeaSummary } from "../types";

type TopIdeasCarouselProps = {
  ideas: IdeaSummary[];
};

function scrollByAmount(container: HTMLDivElement | null, delta: number) {
  if (!container) {
    return;
  }
  container.scrollBy({ left: delta, behavior: "smooth" });
}

export function TopIdeasCarousel({ ideas }: TopIdeasCarouselProps) {
  const trackRef = useRef<HTMLDivElement>(null);

  return (
    <section className="space-y-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-accentSoft">
            Showcase
          </p>
          <h2 className="mt-2 text-3xl font-extrabold text-white">
            Top validated ideas
          </h2>
        </div>
        <div className="flex gap-3">
          <button
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white transition hover:border-accent hover:text-accent"
            onClick={() => scrollByAmount(trackRef.current, -320)}
            type="button"
          >
            Prev
          </button>
          <button
            className="rounded-full border border-white/10 px-4 py-2 text-sm text-white transition hover:border-accent hover:text-accent"
            onClick={() => scrollByAmount(trackRef.current, 320)}
            type="button"
          >
            Next
          </button>
        </div>
      </div>

      <div
        ref={trackRef}
        className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-4"
      >
        {ideas.map((idea) => (
          <article
            key={idea.id}
            className="min-w-[18rem] max-w-sm snap-start rounded-3xl border border-white/10 bg-panel p-5 shadow-card md:min-w-[24rem]"
          >
            <div className="flex items-start justify-between gap-4">
              <span className="rounded-full bg-accent/20 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
                {idea.category}
              </span>
              <span className="rounded-full border border-white/10 px-3 py-1 text-sm text-white">
                {idea.score.toFixed(1)}
              </span>
            </div>
            <h3 className="mt-5 text-xl font-extrabold text-white">
              {idea.title}
            </h3>
            <p className="mt-3 text-sm text-muted">{idea.profession}</p>
            <p className="mt-4 text-sm leading-6 text-slate-200">
              {idea.blueprint.problem_summary}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
