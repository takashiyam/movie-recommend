import type { Genre, Movie, TMDbResponse } from "../types/movie";

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
    region: "JP",
    ...params,
  });
  const res = await fetch(`${BASE_URL}${path}?${searchParams}`);
  if (!res.ok) {
    if (res.status === 401) throw new Error("API_KEY_INVALID");
    throw new Error(`TMDb API error: ${res.status}`);
  }
  return res.json();
}

export async function fetchNowPlaying(page = 1): Promise<TMDbResponse> {
  return fetchTMDb<TMDbResponse>("/movie/now_playing", { page: String(page) });
}

export async function fetchUpcoming(page = 1): Promise<TMDbResponse> {
  return fetchTMDb<TMDbResponse>("/movie/upcoming", { page: String(page) });
}

export async function fetchGenres(): Promise<Genre[]> {
  const data = await fetchTMDb<{ genres: Genre[] }>("/genre/movie/list");
  return data.genres;
}

export interface DiscoverParams {
  genres: number[];
  sortBy: string;
  keywords: string;
  minRating: number;
}

export async function discoverMovies(params: DiscoverParams): Promise<Movie[]> {
  const queryParams: Record<string, string> = {
    sort_by: params.sortBy || "popularity.desc",
    "vote_count.gte": "50",
    page: "1",
  };
  if (params.genres.length > 0) {
    queryParams.with_genres = params.genres.join(",");
  }
  if (params.minRating > 0) {
    queryParams["vote_average.gte"] = String(params.minRating);
  }

  const [page1, page2] = await Promise.all([
    fetchTMDb<TMDbResponse>("/discover/movie", { ...queryParams, page: "1" }),
    fetchTMDb<TMDbResponse>("/discover/movie", { ...queryParams, page: "2" }),
  ]);

  let results = [...page1.results, ...page2.results];

  // If keywords provided, also search and merge
  if (params.keywords) {
    const searchData = await fetchTMDb<TMDbResponse>("/search/movie", {
      query: params.keywords,
      page: "1",
    });
    const existingIds = new Set(results.map((m) => m.id));
    const extraMovies = searchData.results.filter((m) => !existingIds.has(m.id));
    results = [...extraMovies, ...results];
  }

  return results;
}

export function posterUrl(path: string | null, size = "w342"): string {
  if (!path) return "";
  return `https://image.tmdb.org/t/p/${size}${path}`;
}

export function scoreMovie(movie: Movie, favoriteGenres: number[], minRating: number): number {
  let score = 0;

  // Genre match: up to 50 points
  if (favoriteGenres.length > 0) {
    const matchCount = movie.genre_ids.filter((g) => favoriteGenres.includes(g)).length;
    score += (matchCount / Math.max(favoriteGenres.length, 1)) * 50;
  }

  // Rating score: up to 30 points
  score += (movie.vote_average / 10) * 30;

  // Penalty for below minimum rating
  if (movie.vote_average < minRating && movie.vote_count > 10) {
    score -= 20;
  }

  // Popularity bonus: up to 20 points (log scale)
  score += Math.min(Math.log10(movie.popularity + 1) * 7, 20);

  return Math.round(score * 10) / 10;
}
