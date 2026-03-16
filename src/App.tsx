import { useCallback, useState } from "react";
import { ApiKeyForm } from "./components/ApiKeyForm";
import { MovieCard } from "./components/MovieCard";
import { MoodSearch } from "./components/MoodSearch";
import { PreferencesPanel } from "./components/PreferencesPanel";
import { useMovies } from "./hooks/useMovies";
import type { Movie, MovieTab } from "./types/movie";
import { analyzeMood } from "./utils/moodAnalyzer";
import { discoverMovies, scoreMovie } from "./utils/tmdb";

type AppMode = "mood" | "listing";

const tabs: { key: MovieTab; label: string }[] = [
  { key: "now_playing", label: "公開中" },
  { key: "upcoming", label: "公開予定" },
];

export default function App() {
  const {
    tab,
    setTab,
    movies,
    genres,
    loading,
    error,
    preferences,
    setPreferences,
    apiKeySet,
    setApiKey,
    reload,
  } = useMovies();

  const [showPrefs, setShowPrefs] = useState(false);
  const [mode, setMode] = useState<AppMode>("mood");
  const [moodMovies, setMoodMovies] = useState<Movie[]>([]);
  const [moodLoading, setMoodLoading] = useState(false);
  const [moodError, setMoodError] = useState<string | null>(null);
  const [moodLabel, setMoodLabel] = useState<string | null>(null);

  const handleMoodSearch = useCallback(async (mood: string) => {
    setMoodLoading(true);
    setMoodError(null);
    setMoodLabel(null);
    try {
      const analysis = analyzeMood(mood);
      const results = await discoverMovies(analysis);
      setMoodMovies(results);
      setMoodLabel(analysis.label);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      if (msg === "API_KEY_MISSING" || msg === "API_KEY_INVALID") {
        setMoodError("TMDb API キーを確認してください。");
      } else {
        setMoodError(`映画の検索に失敗しました: ${msg}`);
      }
    } finally {
      setMoodLoading(false);
    }
  }, []);

  if (!apiKeySet) {
    return (
      <div className="app">
        <header>
          <h1>映画レコメンド</h1>
          <p className="subtitle">気分にぴったりの映画を見つけよう</p>
        </header>
        <ApiKeyForm onSubmit={setApiKey} error={error} />
      </div>
    );
  }

  const sortedMoodMovies = [...moodMovies].sort((a, b) => {
    const scoreA = scoreMovie(a, preferences.favoriteGenres, preferences.minRating);
    const scoreB = scoreMovie(b, preferences.favoriteGenres, preferences.minRating);
    return scoreB - scoreA;
  });

  const isLoading = mode === "mood" ? moodLoading : loading;
  const currentError = mode === "mood" ? moodError : error;
  const currentMovies = mode === "mood" ? sortedMoodMovies : movies;

  return (
    <div className="app">
      <header>
        <h1>映画レコメンド</h1>
        <p className="subtitle">気分にぴったりの映画を見つけよう</p>
      </header>

      {/* Mode toggle */}
      <nav className="mode-tabs">
        <button
          className={`mode-tab ${mode === "mood" ? "active" : ""}`}
          onClick={() => setMode("mood")}
        >
          気分で探す
        </button>
        <button
          className={`mode-tab ${mode === "listing" ? "active" : ""}`}
          onClick={() => setMode("listing")}
        >
          新作一覧
        </button>
      </nav>

      {mode === "mood" && (
        <MoodSearch onSearch={handleMoodSearch} loading={moodLoading} />
      )}

      {mode === "listing" && (
        <>
          <div className="header-actions">
            <button
              className={`pref-toggle ${showPrefs ? "active" : ""}`}
              onClick={() => setShowPrefs(!showPrefs)}
            >
              好み設定
            </button>
            <button className="reload-btn" onClick={reload} disabled={loading}>
              更新
            </button>
          </div>

          {showPrefs && (
            <PreferencesPanel genres={genres} preferences={preferences} onChange={setPreferences} />
          )}

          <nav className="tabs">
            {tabs.map((t) => (
              <button
                key={t.key}
                className={`tab ${tab === t.key ? "active" : ""}`}
                onClick={() => setTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </>
      )}

      {currentError && <p className="error-text">{currentError}</p>}

      {mode === "mood" && moodLabel && !moodLoading && (
        <div className="mood-result-label">
          <span className="mood-result-icon">&#x1F3AC;</span>
          {moodLabel}
          <span className="mood-result-count">{sortedMoodMovies.length}件</span>
        </div>
      )}

      {isLoading ? (
        <div className="loading">
          <div className="spinner" />
          <p>{mode === "mood" ? "あなたにぴったりの映画を探し中..." : "映画データを取得中..."}</p>
        </div>
      ) : (
        <div className="movie-list">
          {mode === "mood" && currentMovies.length === 0 && !currentError && !moodLabel && (
            <p className="empty mood-empty">上の入力欄から気分を教えてください</p>
          )}
          {currentMovies.length === 0 && moodLabel && (
            <p className="empty">映画が見つかりませんでした。別のキーワードを試してみてください。</p>
          )}
          {mode === "listing" && currentMovies.length === 0 && !currentError && (
            <p className="empty">映画が見つかりませんでした。</p>
          )}
          {currentMovies.map((movie, i) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              genres={genres}
              favoriteGenres={preferences.favoriteGenres}
              minRating={preferences.minRating}
              rank={i + 1}
            />
          ))}
        </div>
      )}

      <footer>
        <p>
          Powered by{" "}
          <a href="https://www.themoviedb.org/" target="_blank" rel="noreferrer">
            TMDb
          </a>
        </p>
      </footer>
    </div>
  );
}
