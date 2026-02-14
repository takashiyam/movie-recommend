import { useCallback, useEffect, useState } from "react";
import type { Genre, Movie, MovieTab, UserPreferences } from "../types/movie";
import { fetchGenres, fetchNowPlaying, fetchUpcoming, scoreMovie } from "../utils/tmdb";

const PREFS_KEY = "movie_recommend_prefs";

function loadPreferences(): UserPreferences {
  try {
    const saved = localStorage.getItem(PREFS_KEY);
    if (saved) return JSON.parse(saved);
  } catch { /* ignore */ }
  return { favoriteGenres: [], minRating: 0 };
}

function savePreferences(prefs: UserPreferences) {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
}

export function useMovies() {
  const [tab, setTab] = useState<MovieTab>("now_playing");
  const [movies, setMovies] = useState<Movie[]>([]);
  const [genres, setGenres] = useState<Genre[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferencesState] = useState<UserPreferences>(loadPreferences);
  const [apiKeySet, setApiKeySet] = useState(() => !!localStorage.getItem("tmdb_api_key"));

  const setPreferences = useCallback((prefs: UserPreferences) => {
    setPreferencesState(prefs);
    savePreferences(prefs);
  }, []);

  const setApiKey = useCallback((key: string) => {
    localStorage.setItem("tmdb_api_key", key);
    setApiKeySet(true);
    setError(null);
  }, []);

  const loadMovies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetcher = tab === "now_playing" ? fetchNowPlaying : fetchUpcoming;
      const [page1, page2] = await Promise.all([fetcher(1), fetcher(2)]);
      setMovies([...page1.results, ...page2.results]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      if (msg === "API_KEY_MISSING") {
        setError("TMDb API キーを設定してください。");
        setApiKeySet(false);
      } else if (msg === "API_KEY_INVALID") {
        setError("API キーが無効です。正しいキーを入力してください。");
        setApiKeySet(false);
      } else {
        setError(`映画データの取得に失敗しました: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    if (apiKeySet) {
      loadMovies();
      fetchGenres().then(setGenres).catch(() => {});
    }
  }, [apiKeySet, loadMovies]);

  const sortedMovies = [...movies].sort((a, b) => {
    const scoreA = scoreMovie(a, preferences.favoriteGenres, preferences.minRating);
    const scoreB = scoreMovie(b, preferences.favoriteGenres, preferences.minRating);
    return scoreB - scoreA;
  });

  return {
    tab,
    setTab,
    movies: sortedMovies,
    genres,
    loading,
    error,
    preferences,
    setPreferences,
    apiKeySet,
    setApiKey,
    reload: loadMovies,
  };
}
