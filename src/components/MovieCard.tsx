import type { Genre, Movie } from "../types/movie";
import { posterUrl, scoreMovie } from "../utils/tmdb";

interface Props {
  movie: Movie;
  genres: Genre[];
  favoriteGenres: number[];
  minRating: number;
  rank: number;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "未定";
  const d = new Date(dateStr + "T00:00:00");
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

function releaseBadge(dateStr: string): { label: string; className: string } | null {
  if (!dateStr) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const release = new Date(dateStr + "T00:00:00");
  const diffDays = Math.round((release.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays < 0 && diffDays >= -14) return { label: "公開中", className: "badge-now" };
  if (diffDays >= 0 && diffDays <= 7) return { label: "まもなく公開", className: "badge-soon" };
  if (diffDays > 7 && diffDays <= 30) return { label: "近日公開", className: "badge-upcoming" };
  return null;
}

export function MovieCard({ movie, genres, favoriteGenres, minRating, rank }: Props) {
  const poster = posterUrl(movie.poster_path);
  const movieGenres = genres.filter((g) => movie.genre_ids.includes(g.id));
  const score = scoreMovie(movie, favoriteGenres, minRating);
  const badge = releaseBadge(movie.release_date);

  return (
    <div className="movie-card">
      <div className="movie-rank">#{rank}</div>
      <div className="movie-poster">
        {poster ? (
          <img src={poster} alt={movie.title} loading="lazy" />
        ) : (
          <div className="no-poster">No Image</div>
        )}
        {badge && <span className={`release-badge ${badge.className}`}>{badge.label}</span>}
      </div>
      <div className="movie-info">
        <h3 className="movie-title">{movie.title}</h3>
        {movie.title !== movie.original_title && (
          <p className="movie-original-title">{movie.original_title}</p>
        )}
        <div className="movie-meta">
          <span className="movie-date">{formatDate(movie.release_date)}</span>
          <span className="movie-rating">
            ★ {movie.vote_average.toFixed(1)}
            <small> ({movie.vote_count})</small>
          </span>
          <span className="movie-score">おすすめ度: {score}</span>
        </div>
        <div className="movie-genres">
          {movieGenres.map((g) => (
            <span
              key={g.id}
              className={`genre-tag ${favoriteGenres.includes(g.id) ? "matched" : ""}`}
            >
              {g.name}
            </span>
          ))}
        </div>
        {movie.overview && <p className="movie-overview">{movie.overview}</p>}
      </div>
    </div>
  );
}
