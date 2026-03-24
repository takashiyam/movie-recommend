import { useCallback, useEffect, useState } from "react";
import type { Drama, Genre, UserPreferences } from "../types/movie";
import { fetchRecentDramas, fetchTvGenres, fetchUpcomingDramas, scoreDrama } from "../utils/tmdb";

type DramaTab = "upcoming" | "recent";

const PREFS_KEY = "drama_schedule_prefs";

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

export function useDramas() {
  const [tab, setTab] = useState<DramaTab>("upcoming");
  const [dramas, setDramas] = useState<Drama[]>([]);
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

  const loadDramas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const fetcher = tab === "upcoming" ? fetchUpcomingDramas : fetchRecentDramas;
      const [page1, page2] = await Promise.all([fetcher(1), fetcher(2)]);
      const allResults = [...page1.results, ...page2.results];
      // Deduplicate by id
      const seen = new Set<number>();
      const unique = allResults.filter((d) => {
        if (seen.has(d.id)) return false;
        seen.add(d.id);
        return true;
      });
      setDramas(unique);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      if (msg === "API_KEY_MISSING") {
        setError("TMDb API キーを設定してください。");
        setApiKeySet(false);
      } else if (msg === "API_KEY_INVALID") {
        setError("API キーが無効です。正しいキーを入力してください。");
        setApiKeySet(false);
      } else {
        setError(`ドラマデータの取得に失敗しました: ${msg}`);
      }
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    if (apiKeySet) {
      loadDramas();
      fetchTvGenres().then(setGenres).catch(() => {});
    }
  }, [apiKeySet, loadDramas]);

  const sortedDramas = [...dramas].sort((a, b) => {
    // Primary sort: by first_air_date ascending for upcoming, descending for recent
    if (tab === "upcoming") {
      const dateCompare = a.first_air_date.localeCompare(b.first_air_date);
      if (dateCompare !== 0) return dateCompare;
    } else {
      const dateCompare = b.first_air_date.localeCompare(a.first_air_date);
      if (dateCompare !== 0) return dateCompare;
    }
    // Secondary sort: by score
    const scoreA = scoreDrama(a, preferences.favoriteGenres, preferences.minRating);
    const scoreB = scoreDrama(b, preferences.favoriteGenres, preferences.minRating);
    return scoreB - scoreA;
  });

  return {
    tab,
    setTab,
    dramas: sortedDramas,
    genres,
    loading,
    error,
    preferences,
    setPreferences,
    apiKeySet,
    setApiKey,
    reload: loadDramas,
  };
}
