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

Open http://localhost:3000 — the browser calls the API at `NEXT_PUBLIC_API_URL`
(default `http://localhost:8001`), so no proxy is involved.

`GET http://localhost:8001/api/health` returns `{"status":"ok","db":true}`; `db:false`
means the API is up but cannot reach Postgres (the startup log says why).

## AI (Groq)

Chat, lead extraction and voice-note transcription all use Groq's hosted API, so the
server needs no local model.

1. Get a key at https://console.groq.com/keys
2. `GROQ_API_KEY=gsk_...` in `server/.env` (model: `GROQ_MODEL`, default
   `llama-3.3-70b-versatile`; voice: `GROQ_STT_MODEL`, default `whisper-large-v3-turbo`)

Offline fallback: the Ollama block is commented out at the bottom of `server/llm.py`.

## Deploy (Render + Vercel)

- **API**: Render web service from this repo, `render.yaml` blueprint (Dockerfile in
  `server/`). It runs `alembic upgrade head` on boot and serves `/api/health`.
  Set `DATABASE_URL` (Supabase session pooler, `?sslmode=require`), `GROQ_API_KEY`,
  `SECRET_KEY`, `BROKER_PASSWORD`, `CLIENT_ORIGIN` (the Vercel URL, no trailing slash)
  and `COOKIE_SECURE=1`.
- **Client**: Vercel project with root directory `client` and
  `NEXT_PUBLIC_API_URL=https://<your-api>.onrender.com`.

The browser talks to the API directly because a ZIP ingest runs for minutes, longer
than a Vercel function lives. That makes the cookie cross-site, hence `COOKIE_SECURE=1`
(SameSite=None; Secure) in production. After deploying Vercel, put its URL in Render's
`CLIENT_ORIGIN`, or login will be rejected by CORS.

## Login

- username: n/a (single admin)
- password: `BROKER_PASSWORD` in `server/.env` (dev default `broker123`)

## Layout

- `client/` — Next.js frontend: landing page, `/login`, `/app` dashboard
- `server/` — FastAPI backend: auth, ZIP ingest, chat, voice notes, customers
