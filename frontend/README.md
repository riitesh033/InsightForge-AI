# InsightForge AI Frontend

The InsightForge AI frontend is a React and TypeScript application for dataset
upload, analysis, cleaning, AI chat, reports, account settings, and billing.

## Development

Install dependencies with `npm install`, then start the development server with
`npm run dev`. Set `VITE_API_URL` to the backend API base URL (including
`/api/v1`); see `.env.example`.

## Validation and preview

- `npm run lint` checks the frontend source.
- `npm run build` type-checks and creates the production bundle in `dist/`.
- `npm run preview` serves the production bundle locally.
