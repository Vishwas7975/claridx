# ClariDx — Frontend Developer Reference

This document provides quick-reference notes and developer workflows for the ClariDx frontend. For the comprehensive project overview, system architecture, database setup, and evaluation reports, see the [root README](../README.md) and [SETUP_AND_TESTING.md](../SETUP_AND_TESTING.md).

## Technology Stack

- **Framework**: React 19 + Vite
- **Language**: TypeScript (~6.0)
- **State & Data Fetching**: TanStack React Query v5 + `openapi-fetch`
- **Testing**: Vitest + Testing Library (`jsdom` environment; requires Node.js ≥ 22.19, Node 24 recommended)
- **Code Style & Formatting**: Prettier + ESLint

## Quick Reference Commands

All commands are executed from the `frontend/` directory:

```bash
# Install Node.js dependencies
npm install

# Start Vite development server (proxies /api to http://127.0.0.1:8000)
npm run dev

# Run comprehensive frontend quality gate (Prettier check, ESLint, Vitest, production build)
npm run check

# Run test suite once
npm test

# Run tests in interactive watch mode
npm run test:watch

# Format codebase with Prettier
npm run format

# Verify formatting without writing changes
npm run format:check

# Run ESLint checks
npm run lint

# Compile production bundle (tsc -b && vite build)
npm run build
```

> **Backend Dependency:** Always start the FastAPI backend first (`uv run uvicorn app.main:app --reload` from `backend/`) before running the dev server or executing the `api:sync` pipeline.

## Typed API Contract Workflow (`api:sync`)

ClariDx maintains end-to-end type safety between the FastAPI backend and React frontend through automated OpenAPI contract generation.

### Architecture

1. **Backend Export**: The backend defines FastAPI endpoints and Pydantic schemas. The script `backend/app/export_openapi.py` serializes the current OpenAPI schema to `frontend/openapi.json`.
2. **TypeScript Generation**: `openapi-typescript` translates `openapi.json` into type definitions in `frontend/src/api/schema.d.ts`.
3. **API Client**: `frontend/src/api/client.ts` wraps `openapi-fetch` with typed paths from `schema.d.ts`, guaranteeing compile-time validation for:
   - Endpoint URLs and HTTP methods
   - Path, query, and request body parameters
   - Response structures, status codes, and error payloads
   - Authentication headers (`Bearer <token>`)

### When and How to Sync

Whenever any backend API route, authentication dependency, or request/response schema changes:

1. Run the unified sync script from `frontend/`:

   ```bash
   npm run api:sync
   ```

   This automatically runs:
   - `npm run api:export` (invokes `uv run python -m app.export_openapi` in `../backend`)
   - `npm run api:types` (runs `openapi-typescript` to regenerate `src/api/schema.d.ts`)

2. Validate the updated contract with the frontend quality gate:

   ```bash
   npm run check
   ```

3. Commit the updated `frontend/openapi.json` and `frontend/src/api/schema.d.ts` alongside the corresponding backend modifications.
