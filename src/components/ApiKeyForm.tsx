import { useState } from "react";

interface Props {
  onSubmit: (key: string) => void;
  error: string | null;
}

export function ApiKeyForm({ onSubmit, error }: Props) {
  const [key, setKey] = useState("");

  return (
    <div className="api-key-form">
      <div className="api-key-card">
        <h2>TMDb API キーを設定</h2>
        <p>
          映画データを取得するために{" "}
          <a href="https://www.themoviedb.org/settings/api" target="_blank" rel="noreferrer">
            TMDb
          </a>{" "}
          の API キー（v3 auth）が必要です。
        </p>
        {error && <p className="error-text">{error}</p>}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (key.trim()) onSubmit(key.trim());
          }}
        >
          <input
            type="text"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="API キーを入力..."
            autoFocus
          />
          <button type="submit" disabled={!key.trim()}>
            設定する
          </button>
        </form>
      </div>
    </div>
  );
}
