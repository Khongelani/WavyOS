# WavyOS

Sales outreach management platform — Angular 17 frontend, FastAPI backend, PostgreSQL database.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

That's it. Everything else runs inside containers.

---

## Run Locally

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd WavyOS
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
OWNER_EMAIL=you@example.com
OWNER_PASSWORD=yourpassword

# Generate a secret: python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=your_random_secret_here

# Optional — leave blank to run in demo mode (no real AI calls)
OPENAI_API_KEY=
```

> The `DATABASE_URL` in `.env.example` is pre-configured for Docker Compose and does not need to change.

### 3. Start the stack

```bash
docker compose up --build
```

This starts three services:

| Service | URL |
|---|---|
| Frontend (Angular) | http://localhost:8080 |
| Backend API | http://localhost:8001 |
| PostgreSQL | localhost:5432 |

The `--build` flag is only needed the first time, or after you change a `Dockerfile` or `requirements.txt`. For subsequent runs:

```bash
docker compose up
```

### 4. Log in

Open http://localhost:8080 and sign in with the `OWNER_EMAIL` and `OWNER_PASSWORD` you set in `.env`.

---

## Development (with hot reload)

The backend already mounts `./backend` as a volume and runs with `--reload`, so Python file changes apply instantly without a rebuild.

For Angular hot reload during development, run the frontend outside Docker:

```bash
# Terminal 1 — start only the backend + database
docker compose up db backend

# Terminal 2 — Angular dev server with proxy to backend
cd frontend
npm install
npm start
```

Then open http://localhost:4200. API calls are proxied to `http://localhost:8000` via `proxy.conf.json`.

---

## Useful Commands

```bash
# View logs for all services
docker compose logs -f

# View logs for a single service
docker compose logs -f backend

# Stop everything
docker compose down

# Stop and delete the database volume (full reset)
docker compose down -v

# Rebuild a single service after code changes
docker compose up --build backend
```

---

## Run Backend Tests

```bash
# From the repo root
docker compose run --rm backend pytest --tb=short -q
```

Or outside Docker (requires a local Postgres instance):

```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://wavy:wavy@localhost:5432/wavyos \
JWT_SECRET=test-secret \
OWNER_EMAIL=test@test.com \
OWNER_PASSWORD=testpassword \
pytest --tb=short -q
```

---

## Run Frontend Tests

```bash
cd frontend
npm install
npm test
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `OWNER_EMAIL` | Yes | Login email for the single owner account |
| `OWNER_PASSWORD` | Yes | Login password |
| `JWT_SECRET` | Yes | Random secret for signing JWT tokens (min 32 chars) |
| `DATABASE_URL` | Yes | PostgreSQL connection string (pre-set for Docker) |
| `OPENAI_API_KEY` | No | OpenAI key — app runs in demo mode without it |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4o`) |
| `ENVIRONMENT` | No | `development` or `production` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins |

---

## Project Structure

```
WavyOS/
├── .env.example          ← copy to .env and fill in
├── docker-compose.yml    ← runs the full stack
├── firebase.json         ← Firebase Hosting config (for deployment)
├── .firebaserc           ← Firebase project reference (for deployment)
├── frontend/             ← Angular 17 app
│   ├── src/
│   ├── Dockerfile
│   └── package.json
└── backend/              ← FastAPI app
    ├── app/
    ├── tests/
    ├── Dockerfile
    └── requirements.txt
```

---

## Deployment

CI/CD is configured via GitHub Actions (`.github/workflows/deploy.yml`). Pushing to `main` or `master` automatically:

1. Runs all tests
2. Deploys the backend to **Google Cloud Run**
3. Deploys the frontend to **Firebase Hosting**

See the [CI/CD setup section](.github/workflows/deploy.yml) for the required GitHub secrets and one-time GCP setup steps.
