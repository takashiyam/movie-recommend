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
