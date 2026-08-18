# AQENO Administration Client

Local-first management UI for AQENO. Communicates exclusively via the [Local Management API](../docs/management/LOCAL_MANAGEMENT_API.md).

## Design

See [ADMIN_CLIENT_DESIGN.md](../docs/management/ADMIN_CLIENT_DESIGN.md) for information architecture, API mapping and API gaps.

## Development

Start the management API (from repository root):

```bash
AQENO_CONFIG_DIR=/tmp/aqeno-api/config \
AQENO_DATA_DIR=/tmp/aqeno-api/data \
AQENO_STATE_DIR=/tmp/aqeno-api/state \
AQENO_MEDIA_DIR=/tmp/aqeno-api/media \
AQENO_MANAGEMENT_KEY=development-only \
.venv/bin/python -m aqeno.management --port 8766
```

Then run the client with Vite for hot reload:

```bash
cd admin
npm install
npm run dev
```

The browser uses `/api/v1` on its own Vite origin; the development server proxies that path to
`127.0.0.1:8766`. This keeps the password/session flow same-origin just like the appliance. The
environment key is only available to automated development and recovery tooling and is never
entered into the UI.

## Device runtime

`npm run build` creates `admin/build/`. The AQENO Management service detects that directory and
serves the static SPA itself behind the reference socket proxy at `http://aqeno.local/` (or the
device IP on port 80 as a diagnostic fallback). No Node/Vite process runs on the device. API and
OpenAPI paths remain below `/api`; direct SPA routes fall back to
`index.html` without masking unknown API routes.

The reference installer runs the build once. `AQENO_ADMIN_DIR` can point to another static build
directory for packaging, but the browser client remains replaceable and contains no backend logic.
Release packaging also carries a generated copy below `aqeno.management/static`, so a wheel does not
need Node or the source checkout at runtime. The repository build takes precedence during local
development.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Development server |
| `npm run build` | Static SPA build |
| `npm run generate:api` | Regenerate TypeScript types from OpenAPI |
| `npm run check` | Typecheck |
| `npm test` | Unit tests |
| `npm run test:e2e` | E2E tests (Playwright) |

## Stack

SvelteKit (static SPA) · TypeScript · Tailwind CSS 4 · TanStack Query · Uppy · Lucide · OpenAPI-generated types
