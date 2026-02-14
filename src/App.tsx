import { useState } from "react";
import { ApiKeyForm } from "./components/ApiKeyForm";
import { MovieCard } from "./components/MovieCard";
import { PreferencesPanel } from "./components/PreferencesPanel";
import { useMovies } from "./hooks/useMovies";
import type { MovieTab } from "./types/movie";

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

  if (!apiKeySet) {
    return (
      <div className="app">
        <header>
          <h1>映画レコメンド</h1>
          <p className="subtitle">日本公開 直前・直後の映画をあなた好みに</p>
        </header>
        <ApiKeyForm onSubmit={setApiKey} error={error} />
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>映画レコメンド</h1>
        <p className="subtitle">日本公開 直前・直後の映画をあなた好みに</p>
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
      </header>

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

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <div className="loading">
          <div className="spinner" />
          <p>映画データを取得中...</p>
        </div>
      ) : (
        <div className="movie-list">
          {movies.length === 0 && !error && <p className="empty">映画が見つかりませんでした。</p>}
          {movies.map((movie, i) => (
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
