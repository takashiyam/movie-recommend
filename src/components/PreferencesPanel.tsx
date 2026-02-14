import type { Genre, UserPreferences } from "../types/movie";

interface Props {
  genres: Genre[];
  preferences: UserPreferences;
  onChange: (prefs: UserPreferences) => void;
}

export function PreferencesPanel({ genres, preferences, onChange }: Props) {
  const toggleGenre = (id: number) => {
    const current = preferences.favoriteGenres;
    const next = current.includes(id) ? current.filter((g) => g !== id) : [...current, id];
    onChange({ ...preferences, favoriteGenres: next });
  };

  return (
    <div className="preferences-panel">
      <h3>好みのジャンル</h3>
      <div className="genre-chips">
        {genres.map((g) => (
          <button
            key={g.id}
            className={`genre-chip ${preferences.favoriteGenres.includes(g.id) ? "active" : ""}`}
            onClick={() => toggleGenre(g.id)}
          >
            {g.name}
          </button>
        ))}
      </div>
      <div className="rating-filter">
        <label>
          最低評価: <strong>{preferences.minRating.toFixed(1)}</strong>
        </label>
        <input
          type="range"
          min="0"
          max="9"
          step="0.5"
          value={preferences.minRating}
          onChange={(e) => onChange({ ...preferences, minRating: Number(e.target.value) })}
        />
      </div>
    </div>
  );
}
