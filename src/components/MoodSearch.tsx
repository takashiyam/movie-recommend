import { useState } from "react";
import { moodSuggestions } from "../utils/moodAnalyzer";

interface MoodSearchProps {
  onSearch: (mood: string) => void;
  loading: boolean;
}

export function MoodSearch({ onSearch, loading }: MoodSearchProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSearch(input.trim());
    }
  };

  const handleSuggestion = (mood: string) => {
    setInput(mood);
    onSearch(mood);
  };

  return (
    <section className="mood-search">
      <div className="mood-header">
        <h2>今の気分は？</h2>
        <p>気分やシーンを入力すると、ぴったりの映画を探します</p>
      </div>
      <form className="mood-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="例: 泣きたい、スカッとしたい、デートで観たい..."
          disabled={loading}
        />
        <button type="submit" disabled={!input.trim() || loading}>
          {loading ? "検索中..." : "探す"}
        </button>
      </form>
      <div className="mood-suggestions">
        {moodSuggestions.map((mood) => (
          <button
            key={mood}
            className="mood-chip"
            onClick={() => handleSuggestion(mood)}
            disabled={loading}
          >
            {mood}
          </button>
        ))}
      </div>
    </section>
  );
}
