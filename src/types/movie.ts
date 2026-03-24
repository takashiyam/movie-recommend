export interface Drama {
  id: number;
  name: string;
  original_name: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  first_air_date: string;
  genre_ids: number[];
  vote_average: number;
  vote_count: number;
  popularity: number;
  origin_country: string[];
  original_language: string;
}

export interface Genre {
  id: number;
  name: string;
}

export interface TMDbTvResponse {
  page: number;
  results: Drama[];
  total_pages: number;
  total_results: number;
}

export interface UserPreferences {
  favoriteGenres: number[];
  minRating: number;
}

export interface CastMember {
  id: number;
  name: string;
  character: string;
  profile_path: string | null;
}

export interface Network {
  id: number;
  name: string;
  logo_path: string | null;
}

export interface Season {
  id: number;
  name: string;
  season_number: number;
  episode_count: number;
  air_date: string | null;
  poster_path: string | null;
}

export interface DramaDetail {
  id: number;
  name: string;
  original_name: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  first_air_date: string;
  genres: Genre[];
  vote_average: number;
  vote_count: number;
  popularity: number;
  status: string;
  number_of_episodes: number | null;
  number_of_seasons: number;
  episode_run_time: number[];
  networks: Network[];
  seasons: Season[];
  homepage: string | null;
  cast: CastMember[];
}
