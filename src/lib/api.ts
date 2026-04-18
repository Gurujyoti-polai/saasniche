import type { IdeaDetail, IdeaSummary, StatsResponse } from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "https://saasniche.onrender.com";

const CACHE_TTL_MS = 5 * 60 * 1000;

type CacheEnvelope<T> = {
  expiresAt: number;
  data: T;
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

function getCached<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as CacheEnvelope<T>;
    if (Date.now() > parsed.expiresAt) {
      localStorage.removeItem(key);
      return null;
    }
    return parsed.data;
  } catch {
    return null;
  }
}

function setCached<T>(key: string, data: T): void {
  try {
    const payload: CacheEnvelope<T> = {
      data,
      expiresAt: Date.now() + CACHE_TTL_MS,
    };
    localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // Ignore cache write issues.
  }
}

export async function fetchStats(): Promise<StatsResponse> {
  const cacheKey = "saasniche_stats";
  const cached = getCached<StatsResponse>(cacheKey);
  if (cached) {
    return cached;
  }
  const data = await fetchJson<StatsResponse>("/stats");
  setCached(cacheKey, data);
  return data;
}

export async function fetchTopIdeas(): Promise<IdeaSummary[]> {
  const cacheKey = "saasniche_top";
  const cached = getCached<IdeaSummary[]>(cacheKey);
  if (cached) {
    return cached;
  }
  const data = await fetchJson<IdeaSummary[]>("/top");
  setCached(cacheKey, data);
  return data;
}

export async function fetchAllIdeas(): Promise<IdeaSummary[]> {
  const pageSize = 50;
  let offset = 0;
  const ideas: IdeaSummary[] = [];

  while (true) {
    const page = await fetchJson<IdeaSummary[]>(
      `/ideas?limit=${pageSize}&offset=${offset}`,
    );
    ideas.push(...page);
    if (page.length < pageSize) {
      break;
    }
    offset += pageSize;
  }

  return ideas;
}

export async function fetchIdeaDetail(id: string): Promise<IdeaDetail> {
  return fetchJson<IdeaDetail>(`/ideas/${id}`);
}

export { API_BASE_URL };
