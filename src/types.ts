export type RevenueModel =
  | "subscription"
  | "usage_based"
  | "freemium"
  | "one_time"
  | "marketplace";

export type TechComplexity = "low" | "medium" | "high";
export type MarketSize = "small" | "medium" | "large";
export type CompetitionLevel = "low" | "medium" | "high";

export type Blueprint = {
  id?: string;
  title?: string;
  target_audience: string;
  problem_summary: string;
  solution: string;
  revenue_model: RevenueModel;
  pricing: string;
  mvp_features: string[];
  tech_complexity: TechComplexity;
  landing_copy: string;
  market_size: MarketSize;
  competition: CompetitionLevel;
};

export type IdeaSummary = {
  id: string;
  title: string;
  subreddit: string;
  url: string;
  score: number;
  category: string;
  profession: string;
  wtp_signal: string;
  blueprint: Blueprint;
};

export type IdeaDetail = IdeaSummary & {
  body: string;
  upvotes?: number;
  intensity?: number;
  scored_at?: string;
};

export type StatsResponse = {
  total_ideas: number;
  avg_score: number;
  top_categories: Record<string, number>;
  top_professions: Record<string, number>;
  score_distribution: Record<string, number>;
};
