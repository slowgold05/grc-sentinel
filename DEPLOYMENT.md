# Portfolio deployment

Recommended split:

- Vercel Hobby: `apps/web` Next.js frontend for the personal, non-commercial demo.
- Railway: `apps/api` Dockerfile plus PostgreSQL with pgvector.
- Ollama: local private workflow. A hosted API may use the existing OpenAI-compatible provider;
  never send real customer policy data from the portfolio demo.

Live services:

- Frontend: https://grc-sentinel-slowgold05s-projects.vercel.app
- API health: https://api-production-3fd2d.up.railway.app/health

## Railway

Create PostgreSQL and API services from this repository. Set the API Dockerfile path to
`apps/api/Dockerfile` and its health check to `/health`. Configure secrets in Railway, never Git:

```text
DATABASE_URL
MIGRATION_DATABASE_URL
APP_DATABASE_PASSWORD
UPLOAD_MASTER_KEY_BASE64
CLERK_SECRET_KEY
CLERK_AUTHORIZED_PARTIES
LLM_BASE_URL
LLM_API_KEY
LLM_GENERATION_MODEL
LLM_VERIFIER_MODEL
OLLAMA_BASE_URL
OLLAMA_EMBEDDING_MODEL
```

Use Railway's private PostgreSQL host for `DATABASE_URL`. `deploy.py` creates the restricted
application role, runs migrations through `MIGRATION_DATABASE_URL`, grants application access,
and then starts the API as that restricted role.

## Vercel

Import the GitHub repository with Root Directory `apps/web`. Keep source files outside the root
included so the root pnpm lockfile is available. Configure:

```text
NEXT_PUBLIC_API_URL=https://your-railway-api-domain
NEXT_PUBLIC_APP_URL=https://your-vercel-domain
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your-production-publishable-key
```

Add both production domains to Clerk and set the Vercel origin in `CLERK_AUTHORIZED_PARTIES`.
Enable Organizations and email authentication. Google and GitHub are optional conveniences;
production OAuth requires provider-owned credentials.

## Final checks

1. `/`, `/sign-in`, and API `/health` return 200.
2. Create a Clerk organization and confirm `/api/tenant` provisions it once.
3. Create an engagement, upload a non-sensitive sample policy, and verify coverage.
4. Confirm a signed-out request to `/api/tenant` returns 401.
5. Record the flow using `DEMO.md` and replace the README screenshot if needed.
