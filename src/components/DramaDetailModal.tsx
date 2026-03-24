import { useEffect, useState } from "react";
import type { DramaDetail } from "../types/movie";
import { fetchDramaDetail, posterUrl } from "../utils/tmdb";

interface Props {
  dramaId: number;
  onClose: () => void;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "未定";
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

export function DramaDetailModal({ dramaId, onClose }: Props) {
  const [detail, setDetail] = useState<DramaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchDramaDetail(dramaId)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "取得に失敗しました");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [dramaId]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <button className="modal-close" onClick={onClose}>✕</button>

        {loading && (
          <div className="loading">
            <div className="spinner" />
            <p>読み込み中...</p>
          </div>
        )}

        {error && <p className="error-text">{error}</p>}

        {detail && (
          <>
            {detail.backdrop_path && (
              <div className="modal-backdrop-img">
                <img
                  src={posterUrl(detail.backdrop_path, "w780")}
                  alt=""
                />
              </div>
            )}

            <div className="modal-body">
              <div className="modal-header-row">
                {detail.poster_path && (
                  <img
                    className="modal-poster"
                    src={posterUrl(detail.poster_path, "w185")}
                    alt={detail.name}
                  />
                )}
                <div className="modal-title-area">
                  <h2 className="modal-title">{detail.name}</h2>
                  {detail.name !== detail.original_name && (
                    <p className="modal-original-title">{detail.original_name}</p>
                  )}
                  <div className="modal-meta-tags">
                    {detail.vote_average > 0 && (
                      <span className="modal-rating">★ {detail.vote_average.toFixed(1)}</span>
                    )}
                    <span className="modal-date">{formatDate(detail.first_air_date)}</span>
                    {detail.status && <span className="modal-status">{detail.status}</span>}
                  </div>
                </div>
              </div>

              {detail.networks.length > 0 && (
                <div className="modal-section">
                  <h4>放送局</h4>
                  <div className="modal-networks">
                    {detail.networks.map((n) => (
                      <span key={n.id} className="network-tag">{n.name}</span>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-section">
                <h4>番組情報</h4>
                <div className="modal-info-grid">
                  {detail.number_of_seasons > 0 && (
                    <div className="info-item">
                      <span className="info-label">シーズン</span>
                      <span className="info-value">{detail.number_of_seasons}</span>
                    </div>
                  )}
                  {detail.number_of_episodes != null && detail.number_of_episodes > 0 && (
                    <div className="info-item">
                      <span className="info-label">エピソード数</span>
                      <span className="info-value">{detail.number_of_episodes}</span>
                    </div>
                  )}
                  {detail.episode_run_time.length > 0 && (
                    <div className="info-item">
                      <span className="info-label">放送時間</span>
                      <span className="info-value">{detail.episode_run_time[0]}分</span>
                    </div>
                  )}
                </div>
              </div>

              {detail.genres.length > 0 && (
                <div className="modal-section">
                  <h4>ジャンル</h4>
                  <div className="drama-genres">
                    {detail.genres.map((g) => (
                      <span key={g.id} className="genre-tag">{g.name}</span>
                    ))}
                  </div>
                </div>
              )}

              {detail.overview && (
                <div className="modal-section">
                  <h4>あらすじ</h4>
                  <p className="modal-overview">{detail.overview}</p>
                </div>
              )}

              {detail.cast.length > 0 && (
                <div className="modal-section">
                  <h4>キャスト</h4>
                  <div className="modal-cast-list">
                    {detail.cast.map((c) => (
                      <div key={c.id} className="cast-item">
                        <div className="cast-photo">
                          {c.profile_path ? (
                            <img src={posterUrl(c.profile_path, "w92")} alt={c.name} />
                          ) : (
                            <div className="cast-no-photo" />
                          )}
                        </div>
                        <div className="cast-info">
                          <span className="cast-name">{c.name}</span>
                          {c.character && (
                            <span className="cast-character">{c.character}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {detail.homepage && (
                <div className="modal-section">
                  <a
                    href={detail.homepage}
                    target="_blank"
                    rel="noreferrer"
                    className="modal-link"
                  >
                    公式サイトを開く
                  </a>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
