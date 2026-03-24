import type { Drama, Genre, TMDbTvResponse } from "../types/movie";

const BASE_URL = "https://api.themoviedb.org/3";

function getApiKey(): string {
  return localStorage.getItem("tmdb_api_key") || "";
}

async function fetchTMDb<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const apiKey = getApiKey();
  if (!apiKey) {
    throw new Error("API_KEY_MISSING");
  }
  const searchParams = new URLSearchParams({
    api_key: apiKey,
    language: "ja-JP",
    ...params,
  });
  const res = await fetch(`${BASE_URL}${path}?${searchParams}`);
  if (!res.ok) {
    if (res.status === 401) throw new Error("API_KEY_INVALID");
    throw new Error(`TMDb API error: ${res.status}`);
  }
  return res.json();
}

function formatDateParam(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Fetch Japanese TV dramas premiering within the next month */
export async function fetchUpcomingDramas(page = 1): Promise<TMDbTvResponse> {
  const today = new Date();
  const oneMonthLater = new Date();
  oneMonthLater.setMonth(oneMonthLater.getMonth() + 1);

  return fetchTMDb<TMDbTvResponse>("/discover/tv", {
    with_origin_country: "JP",
    with_original_language: "ja",
    "first_air_date.gte": formatDateParam(today),
    "first_air_date.lte": formatDateParam(oneMonthLater),
    without_genres: "16",
    sort_by: "first_air_date.asc",
    timezone: "Asia/Tokyo",
    page: String(page),
  });
}

/** Fetch Japanese TV dramas that recently started airing (past 2 weeks) */
export async function fetchRecentDramas(page = 1): Promise<TMDbTvResponse> {
  const today = new Date();
  const twoWeeksAgo = new Date();
  twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);

  return fetchTMDb<TMDbTvResponse>("/discover/tv", {
    with_origin_country: "JP",
    with_original_language: "ja",
    "first_air_date.gte": formatDateParam(twoWeeksAgo),
    "first_air_date.lte": formatDateParam(today),
    without_genres: "16",
    sort_by: "first_air_date.desc",
    timezone: "Asia/Tokyo",
    page: String(page),
  });
}

export async function fetchTvGenres(): Promise<Genre[]> {
  const data = await fetchTMDb<{ genres: Genre[] }>("/genre/tv/list");
  return data.genres;
}

export function posterUrl(path: string | null, size = "w342"): string {
  if (!path) return "";
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function scoreDrama(drama: Drama, favoriteGenres: number[], minRating: number): number {
  let score = 0;

  // Genre match: up to 50 points
  if (favoriteGenres.length > 0) {
    const matchCount = drama.genre_ids.filter((g) => favoriteGenres.includes(g)).length;
    score += (matchCount / Math.max(favoriteGenres.length, 1)) * 50;
  }

  // Rating score: up to 30 points
  score += (drama.vote_average / 10) * 30;

  // Penalty for below minimum rating
  if (drama.vote_average < minRating && drama.vote_count > 10) {
    score -= 20;
  }

  // Popularity bonus: up to 20 points (log scale)
  score += Math.min(Math.log10(drama.popularity + 1) * 7, 20);

  return Math.round(score * 10) / 10;
}
