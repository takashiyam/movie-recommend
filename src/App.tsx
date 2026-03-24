import { useState } from "react";
import { ApiKeyForm } from "./components/ApiKeyForm";
import { DramaCard } from "./components/DramaCard";
import { DramaDetailModal } from "./components/DramaDetailModal";
import { PreferencesPanel } from "./components/PreferencesPanel";
import { useDramas } from "./hooks/useMovies";

const tabs = [
  { key: "upcoming" as const, label: "放送予定" },
  { key: "recent" as const, label: "最近開始" },
];

export default function App() {
  const {
    tab,
    setTab,
    dramas,
    genres,
    loading,
    error,
    preferences,
    setPreferences,
    apiKeySet,
    setApiKey,
    reload,
  } = useDramas();

  const [showPrefs, setShowPrefs] = useState(false);
  const [selectedDramaId, setSelectedDramaId] = useState<number | null>(null);

  if (!apiKeySet) {
    return (
      <div className="app">
        <header>
          <h1>日本ドラマ新番組ガイド</h1>
          <p className="subtitle">この先1ヶ月に放送開始する日本のテレビドラマ</p>
        </header>
        <ApiKeyForm onSubmit={setApiKey} error={error} />
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <h1>日本ドラマ新番組ガイド</h1>
        <p className="subtitle">この先1ヶ月に放送開始する日本のテレビドラマ</p>
        <div className="header-actions">
          <button
            className={`pref-toggle ${showPrefs ? "active" : ""}`}
            onClick={() => setShowPrefs(!showPrefs)}
          >
            ジャンル絞込
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
          <p>ドラマデータを取得中...</p>
        </div>
      ) : (
        <>
          <p className="result-count">
            {dramas.length > 0
              ? `${dramas.length}件のドラマが見つかりました`
              : ""}
          </p>
          <div className="drama-list">
            {dramas.length === 0 && !error && (
              <p className="empty">該当するドラマが見つかりませんでした。</p>
            )}
            {dramas.map((drama) => (
              <DramaCard
                key={drama.id}
                drama={drama}
                genres={genres}
                favoriteGenres={preferences.favoriteGenres}
                onClick={() => setSelectedDramaId(drama.id)}
              />
            ))}
          </div>
        </>
      )}

      {selectedDramaId !== null && (
        <DramaDetailModal
          dramaId={selectedDramaId}
          onClose={() => setSelectedDramaId(null)}
        />
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
