# BrokerDesk

Web app for rental property brokers: keeps WhatsApp as the workflow, puts all the data in one dashboard.

## Run

```bash
# terminal 1 — API (FastAPI, port 8000)
cd server
uv venv --python 3.11 .venv
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
.venv\Scripts\uvicorn.exe main:app --port 8000 --host 127.0.0.1

# terminal 2 — frontend (Next.js, port 3000)
cd client
npm run dev
```

Open http://localhost:3000

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
