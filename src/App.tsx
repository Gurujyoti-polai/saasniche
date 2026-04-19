import type { ReactNode } from "react";
import { type ChangeEvent, useEffect, useState } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { IdeaCard } from "./components/IdeaCard";
import { IdeaDetailModal } from "./components/IdeaDetailModal";
import { CardSkeleton, HeroSkeleton } from "./components/Skeletons";
import { StatCard } from "./components/StatCard";
import { TopIdeasCarousel } from "./components/TopIdeasCarousel";
import { API_BASE_URL, fetchAllIdeas, fetchIdeaDetail, fetchStats, fetchTopIdeas } from "./lib/api";
import type { IdeaDetail, IdeaSummary, StatsResponse } from "./types";

const ITEMS_PER_PAGE = 50;
const DEFAULT_TOTAL_IDEAS = 287;

type SortOption = "score_desc" | "score_asc" | "newest";

function scoreToBase36(id: string): number {
  const parsed = parseInt(id, 36);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function sortIdeas(ideas: IdeaSummary[], sort: SortOption): IdeaSummary[] {
  const next = [...ideas];
  if (sort === "score_asc") {
    next.sort((left, right) => left.score - right.score);
    return next;
  }
  if (sort === "newest") {
    next.sort((left, right) => scoreToBase36(right.id) - scoreToBase36(left.id));
    return next;
  }
  next.sort((left, right) => right.score - left.score);
  return next;
}

function useDebouncedValue<T>(value: T, delayMs: number) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(handle);
  }, [delayMs, value]);

  return debounced;
}

function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,107,53,0.2),_transparent_28%),linear-gradient(180deg,_#0f1729_0%,_#10192c_48%,_#0a1020_100%)] text-white">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <Link className="text-xl font-extrabold tracking-tight text-white" to="/">
          SaasNiche
        </Link>
        <nav className="flex items-center gap-3">
          <Link
            className="rounded-full border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-accent hover:text-accent"
            to="/ideas"
          >
            Dashboard
          </Link>
          <a
            className="rounded-full bg-white px-4 py-2 text-sm font-bold text-ink transition hover:bg-accent hover:text-white"
            href="https://github.com/"
            rel="noreferrer"
            target="_blank"
          >
            GitHub
          </a>
        </nav>
      </header>
      {children}
    </div>
  );
}

function LandingPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [topIdeas, setTopIdeas] = useState<IdeaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        const [statsData, topData] = await Promise.all([fetchStats(), fetchTopIdeas()]);
        if (cancelled) {
          return;
        }
        setStats(statsData);
        setTopIdeas(topData);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load landing page.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const topCategory = stats ? Object.keys(stats.top_categories)[0] ?? "workflow" : "workflow";
  const totalIdeas = stats?.total_ideas ?? DEFAULT_TOTAL_IDEAS;

  return (
    <AppShell>
      <main className="mx-auto max-w-7xl space-y-16 px-6 pb-20 pt-10 lg:px-8">
        <section className="grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-accentSoft">
              SaaS idea intelligence
            </p>
            <h1 className="mt-4 max-w-4xl text-5xl font-black leading-[0.95] text-white sm:text-6xl lg:text-7xl">
              Turn Reddit Pain Points into SaaS Ideas
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              {totalIdeas} validated ideas from real developers, founders, and makers.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link
                className="rounded-full bg-white px-6 py-3 text-base font-bold text-ink transition hover:bg-accent hover:text-white"
                to="/ideas"
              >
                Explore Ideas
              </Link>
              <a
                className="rounded-full border border-white/10 px-6 py-3 text-base font-semibold text-slate-200 transition hover:border-accent hover:text-accent"
                href={API_BASE_URL}
                rel="noreferrer"
                target="_blank"
              >
                View API
              </a>
            </div>
          </div>
          <div className="rounded-[2rem] border border-white/10 bg-panel/90 p-6 shadow-card">
            {loading ? (
              <HeroSkeleton />
            ) : error ? (
              <p className="text-sm text-orange-300">{error}</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-3">
                <StatCard label="Total Ideas" value={String(totalIdeas)} accent />
                <StatCard label="Avg Score" value={String(stats?.avg_score ?? 0)} />
                <StatCard label="Top Category" value={topCategory} />
              </div>
            )}
          </div>
        </section>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <CardSkeleton key={index} />
            ))}
          </div>
        ) : (
          <TopIdeasCarousel ideas={topIdeas} />
        )}

        <footer className="flex flex-col items-start justify-between gap-5 rounded-[2rem] border border-white/10 bg-panel px-6 py-5 shadow-card md:flex-row md:items-center">
          <div>
            <p className="text-base font-extrabold text-white">Built for founder-grade discovery</p>
            <p className="mt-1 text-sm text-muted">
              Explore real demand before you build.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <a
              className="rounded-full border border-white/10 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-accent hover:text-accent"
              href="https://github.com/"
              rel="noreferrer"
              target="_blank"
            >
              GitHub
            </a>
            <span className="rounded-full bg-accent px-4 py-2 text-sm font-bold text-white">
              Built with Ollama
            </span>
          </div>
        </footer>
      </main>
    </AppShell>
  );
}

function DashboardPage() {
  const [ideas, setIdeas] = useState<IdeaSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [profession, setProfession] = useState("all");
  const [minScore, setMinScore] = useState(25);
  const [sort, setSort] = useState<SortOption>("score_desc");
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);
  const [selectedIdea, setSelectedIdea] = useState<IdeaSummary | null>(null);
  const [ideaDetail, setIdeaDetail] = useState<IdeaDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        const [ideaData, statsData] = await Promise.all([fetchAllIdeas(), fetchStats()]);
        if (cancelled) {
          return;
        }
        setIdeas(ideaData);
        setStats(statsData);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load ideas.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setVisibleCount(ITEMS_PER_PAGE);
  }, [debouncedQuery, category, profession, minScore, sort]);

  useEffect(() => {
    if (!selectedIdea) {
      setIdeaDetail(null);
      return;
    }

    const ideaId = selectedIdea.id;
    let cancelled = false;

    async function loadDetail() {
      try {
        setDetailLoading(true);
        const detail = await fetchIdeaDetail(ideaId);
        if (!cancelled) {
          setIdeaDetail(detail);
        }
      } catch {
        if (!cancelled) {
          setIdeaDetail(null);
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    }

    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedIdea]);

  const categories = stats ? Object.keys(stats.top_categories) : [];
  const professions = stats ? Object.keys(stats.top_professions) : [];

  const filtered = sortIdeas(
    ideas.filter((idea) => {
      const searchable = `${idea.title} ${idea.blueprint.problem_summary}`.toLowerCase();
      return (
        searchable.includes(debouncedQuery.toLowerCase()) &&
        (category === "all" || idea.category === category) &&
        (profession === "all" || idea.profession === profession) &&
        idea.score >= minScore
      );
    }),
    sort,
  );

  const visibleIdeas = filtered.slice(0, visibleCount);
  const canLoadMore = visibleCount < filtered.length;

  function handleQueryChange(event: ChangeEvent<HTMLInputElement>) {
    setQuery(event.target.value);
  }

  function openIdea(idea: IdeaSummary) {
    setSelectedIdea(idea);
    setIdeaDetail(null);
  }

  return (
    <AppShell>
      <main className="mx-auto max-w-7xl px-6 pb-16 pt-6 lg:px-8">
        <section className="sticky top-0 z-20 mb-8 rounded-[2rem] border border-white/10 bg-ink/85 p-4 shadow-card backdrop-blur-xl">
          <div className="grid gap-3 lg:grid-cols-[2fr_1fr_1fr_1fr_1fr]">
            <input
              className="rounded-2xl border border-white/10 bg-panel px-4 py-3 text-white outline-none transition focus:border-accent"
              onChange={handleQueryChange}
              placeholder="Search by title or problem summary"
              value={query}
            />
            <select
              className="rounded-2xl border border-white/10 bg-panel px-4 py-3 text-white outline-none focus:border-accent"
              onChange={(event) => setCategory(event.target.value)}
              value={category}
            >
              <option value="all">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <select
              className="rounded-2xl border border-white/10 bg-panel px-4 py-3 text-white outline-none focus:border-accent"
              onChange={(event) => setProfession(event.target.value)}
              value={profession}
            >
              <option value="all">All professions</option>
              {professions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
            <label className="rounded-2xl border border-white/10 bg-panel px-4 py-3 text-white">
              <span className="mb-2 block text-xs uppercase tracking-[0.18em] text-muted">
                Score {minScore}+
              </span>
              <input
                className="w-full accent-accent"
                max={100}
                min={25}
                onChange={(event) => setMinScore(Number(event.target.value))}
                type="range"
                value={minScore}
              />
            </label>
            <select
              className="rounded-2xl border border-white/10 bg-panel px-4 py-3 text-white outline-none focus:border-accent"
              onChange={(event) => setSort(event.target.value as SortOption)}
              value={sort}
            >
              <option value="score_desc">Score (High→Low)</option>
              <option value="score_asc">Score (Low→High)</option>
              <option value="newest">Newest</option>
            </select>
          </div>
        </section>

        {loading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <CardSkeleton key={index} />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-3xl border border-orange-400/20 bg-orange-500/10 p-6 text-orange-200">
            {error}
          </div>
        ) : (
          <>
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm uppercase tracking-[0.2em] text-muted">
                  Searchable dashboard
                </p>
                <p className="mt-2 text-base text-slate-200">
                  Showing {visibleIdeas.length} of {filtered.length} ideas.
                </p>
              </div>
              <div className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-200">
                50 per batch
              </div>
            </div>

            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {visibleIdeas.map((idea) => (
                <IdeaCard key={idea.id} idea={idea} onView={openIdea} />
              ))}
            </div>

            {canLoadMore ? (
              <div className="mt-10 flex items-center justify-center">
                <button
                  className="rounded-full bg-white px-6 py-3 text-sm font-bold text-ink transition hover:bg-accent hover:text-white"
                  onClick={() =>
                    setVisibleCount((value) => Math.min(value + ITEMS_PER_PAGE, filtered.length))
                  }
                  type="button"
                >
                  Load More
                </button>
              </div>
            ) : null}
          </>
        )}
      </main>

      <IdeaDetailModal
        idea={ideaDetail}
        loading={detailLoading}
        onClose={() => {
          setSelectedIdea(null);
          setIdeaDetail(null);
        }}
      />
    </AppShell>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<LandingPage />} path="/" />
      <Route element={<DashboardPage />} path="/ideas" />
      <Route element={<Navigate replace to="/" />} path="*" />
    </Routes>
  );
}
