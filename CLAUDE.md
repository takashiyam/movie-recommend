# CLAUDE.md

## Project Overview

Japanese movie recommendation web app that shows now-playing and upcoming films using the TMDb API. Users set preferences (favorite genres, minimum rating) and movies are scored/ranked by relevance. The entire UI is in Japanese targeting Japanese-speaking users.

**Live site:** Deployed to GitHub Pages at `/movie-recommend/`

## Tech Stack

- **Framework:** React 19 + TypeScript ~5.9
- **Build tool:** Vite 7
- **Styling:** Plain CSS with CSS custom properties (dark theme)
- **Linting:** ESLint 9 (flat config) with TypeScript and React plugins
- **Deployment:** GitHub Actions → GitHub Pages (on push to `main`)
- **Node version:** 22 (per CI config)

## Commands

```bash
npm run dev       # Start dev server with HMR
npm run build     # TypeScript check (tsc -b) + Vite production build
npm run lint      # ESLint on all files
npm run preview   # Preview production build locally
```

There are no tests configured in this project.

## Project Structure

```
src/
├── components/
│   ├── ApiKeyForm.tsx      # TMDb API key input modal
│   ├── MovieCard.tsx       # Individual movie display card
│   └── PreferencesPanel.tsx # Genre/rating preference controls
├── hooks/
│   └── useMovies.ts        # Core data fetching & state logic
├── types/
│   └── movie.ts            # TypeScript interfaces (Movie, Genre, UserPreferences, MovieTab)
├── utils/
│   └── tmdb.ts             # TMDb API wrapper & scoring algorithm
├── App.tsx                 # Root component with tab navigation
├── main.tsx                # React entry point
└── index.css               # Global styles with CSS variables
```

## Architecture & Key Patterns

- **Functional components only** — no class components
- **Custom hooks** for business logic (`useMovies` centralizes fetching, preferences, scoring)
- **Direct fetch API** — no axios or other HTTP library
- **localStorage** for persistence: `tmdb_api_key` (API key), `movie_recommend_prefs` (user preferences)
- **No external state management** — React hooks only (`useState`, `useEffect`, `useCallback`)
- **No routing library** — tab-based navigation within `App.tsx`

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase files and exports | `MovieCard.tsx` |
| Hooks | `use` prefix, camelCase | `useMovies.ts` |
| Utility functions | camelCase | `fetchNowPlaying`, `scoreMovie` |
| TypeScript interfaces | PascalCase | `Movie`, `UserPreferences` |
| CSS classes | kebab-case | `.movie-card`, `.genre-chip` |

## TypeScript Configuration

- **Strict mode enabled** — all strict checks are on
- `noUnusedLocals: true` — unused local variables are errors
- `noUnusedParameters: true` — unused parameters are errors
- `noFallthroughCasesInSwitch: true`
- Module resolution: `bundler`
- Target: ES2022

## External Dependencies

- **TMDb API** (`https://api.themoviedb.org/3`) — sole external data source
  - API key is entered by the user at runtime (not a build secret)
  - Language: `ja-JP`, Region: `JP`
  - Endpoints: `/movie/now_playing`, `/movie/upcoming`, `/genre/movie/list`
  - Image CDN: `https://image.tmdb.org/t/p/{size}{path}`

## CI/CD

GitHub Actions workflow (`.github/workflows/deploy.yml`):
- Triggers on push to `main`
- Runs `npm ci` → `npm run build` → deploys `dist/` to GitHub Pages
- Node 22, npm cache enabled

## Code Style Notes

- All user-facing strings are in Japanese
- CSS uses custom properties defined in `:root` (dark theme with indigo accent `#6366f1`)
- Mobile-first responsive design with 600px breakpoint
- iOS PWA meta tags included for home-screen support
- Vite `base` is set to `/movie-recommend/` for GitHub Pages path
