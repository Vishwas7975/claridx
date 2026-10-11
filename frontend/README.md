# ClariDx frontend

React + TypeScript + Vite. The API contract lives in `openapi.json`, exported by the backend;
TypeScript types in `src/api/schema.d.ts` are generated from it.

    npm install          install dependencies
    npm run dev          dev server (proxies /api to http://127.0.0.1:8000)
    npm run check        format check, lint, tests and production build
    npm run api:sync     re-export the API contract and regenerate the types
                         (run after any backend API change, then commit the result)

Start the backend first (`uv run uvicorn app.main:app --reload` in `../backend`).
