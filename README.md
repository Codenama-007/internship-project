# BrokerDesk

Web app for rental property brokers: keeps WhatsApp as the workflow, puts all the data in one dashboard.

## Run locally

```bash
# 1) database: Postgres 16 in Docker
#    Port 5432 must be free. If a local Postgres already runs there, stop it or
#    change the host port in docker-compose.yml and in DATABASE_URL.
docker compose up -d

# 2) config
cd server
cp .env.example .env     # then fill in DATABASE_URL, BROKER_PASSWORD, SECRET_KEY
uv venv --python 3.11 .venv
uv pip install -r requirements.txt --python .venv/Scripts/python.exe

# 3) tables
.venv\Scripts\alembic.exe upgrade head

# 4) API on 8001 (8000 is reserved on some Windows machines -> WinError 10013)
.venv\Scripts\uvicorn.exe main:app --reload --port 8001 --host 127.0.0.1

# 5) client, new terminal
cd client
npm run dev
```

Open http://localhost:3000 — it proxies `/api/*` to `http://localhost:8001`.
If the API runs elsewhere, set `NEXT_PUBLIC_API_URL` in `client/.env.local` before
starting the client.

`GET http://localhost:8001/api/health` returns `{"status":"ok","db":true}`; `db:false`
means the API is up but cannot reach Postgres (the startup log says why).

## Chat (local LLM)

The chat calls a local Ollama instance — no API key, no cloud.

```bash
ollama serve                 # usually already running
ollama pull llama3.2:3b      # or set OLLAMA_MODEL in server/.env to another pulled model
```

`OLLAMA_URL` and `OLLAMA_MODEL` live in `server/.env`.

## Login

- username: n/a (single admin)
- password: `BROKER_PASSWORD` in `server/.env` (dev default `broker123`)

## Layout

- `client/` — Next.js frontend: landing page, `/login`, `/app` dashboard shell
- `server/` — FastAPI backend: auth now, ingestion + AI agent endpoints next
