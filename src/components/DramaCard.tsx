import type { Drama, Genre } from "../types/movie";
import { posterUrl } from "../utils/tmdb";
import { getDayOfWeek } from "../utils/calendar";

interface Props {
  drama: Drama;
  genres: Genre[];
  favoriteGenres: number[];
  onClick?: () => void;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "未定";
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

function airBadge(dateStr: string): { label: string; className: string } | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const airDate = new Date(dateStr + "T00:00:00");
  const diffDays = Math.round((airDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0 && diffDays >= -14) return { label: "放送中", className: "badge-now" };
  if (diffDays >= 0 && diffDays <= 3) return { label: "まもなく開始", className: "badge-soon" };
  if (diffDays > 3 && diffDays <= 14) return { label: "今期スタート", className: "badge-upcoming" };
  if (diffDays > 14) return { label: "来期スタート", className: "badge-future" };
  return null;
}

function daysUntilAir(dateStr: string): string {
  if (!dateStr) return "";
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const airDate = new Date(dateStr + "T00:00:00");
  const diffDays = Math.round((airDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "今日放送開始";
  if (diffDays === 1) return "明日放送開始";
  if (diffDays > 1) return `あと${diffDays}日`;
  if (diffDays >= -1) return "昨日開始";
  return `${Math.abs(diffDays)}日前に開始`;
}

export function DramaCard({ drama, genres, favoriteGenres, onClick }: Props) {
  const poster = posterUrl(drama.poster_path);
  const dramaGenres = genres.filter((g) => drama.genre_ids.includes(g.id));
  const badge = airBadge(drama.first_air_date);
  const countdown = daysUntilAir(drama.first_air_date);

  return (
    <div className="drama-card" onClick={onClick} role={onClick ? "button" : undefined} tabIndex={onClick ? 0 : undefined}>
      <div className="drama-poster">
        {poster ? (
          <img src={poster} alt={drama.name} loading="lazy" />
        ) : (
          <div className="no-poster">No Image</div>
        )}
        {badge && <span className={`release-badge ${badge.className}`}>{badge.label}</span>}
      </div>
      <div className="drama-info">
        <h3 className="drama-title">{drama.name}</h3>
        {drama.name !== drama.original_name && (
          <p className="drama-original-title">{drama.original_name}</p>
        )}
        <div className="drama-meta">
          <span className="drama-date">{formatDate(drama.first_air_date)}({getDayOfWeek(drama.first_air_date)})</span>
          {countdown && <span className="drama-countdown">{countdown}</span>}
          {drama.vote_average > 0 && (
            <span className="drama-rating">
              ★ {drama.vote_average.toFixed(1)}
              <small> ({drama.vote_count})</small>
            </span>
          )}
        </div>
        <div className="drama-genres">
          {dramaGenres.map((g) => (
            <span
              key={g.id}
              className={`genre-tag ${favoriteGenres.includes(g.id) ? "matched" : ""}`}
            >
              {g.name}
            </span>
          ))}
        </div>
        {drama.overview && <p className="drama-overview">{drama.overview}</p>}
      </div>
    </div>
  );
}
