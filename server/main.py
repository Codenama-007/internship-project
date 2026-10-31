import os
import tempfile
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

from auth import check_password, clear_session, current_user, issue_token, set_session
from audio import MAX_AUDIO, transcribe
from db import BROKER_ID, Customer, Session, engine
from graph import ingestion_graph, thread_id
from groq import APIError
from llm import MODEL, reply
from nodes import save_typed
from schemas import (
    ChatBody,
    ChatOut,
    CustomerOut,
    IngestOut,
    LoginBody,
    LoginOut,
    MeOut,
    OkOut,
)
from whatsapp import MAX_ZIP


def database_reason(exc: Exception) -> str:
    """Readable cause without the password or the full URL."""
    message = str(getattr(exc, "orig", exc)).lower()
    if "password authentication failed" in message or "authentication failed" in message:
        return "wrong password in DATABASE_URL"
    if "does not exist" in message:
        return "database does not exist (create it, or run: docker compose up -d)"
    if "could not connect" in message or "connection refused" in message or "timeout" in message:
        return "Postgres is not running on the configured host/port"
    return "cannot connect to Postgres"


def db_ok(verbose: bool = False) -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except OperationalError as exc:
        if verbose:
            print(f"[db] {database_reason(exc)}", flush=True)
        return False
    except Exception:
        if verbose:
            print("[db] connection check failed", flush=True)
        return False
    
def llm_ok(verbose: bool = False) -> bool:
    """Groq only needs a key: no local server to start."""
    if os.getenv("GROQ_API_KEY"):
        return True
    if verbose:
        print("[ai] GROQ_API_KEY is not set - chat, ingest and voice notes will fail", flush=True)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if db_ok(verbose=True):
        print("[db] Postgres reachable", flush=True)
    if llm_ok(verbose=True):
        print(f"[ai] Groq ready, model {MODEL}", flush=True)
    yield


app = FastAPI(title="BrokerDesk", lifespan=lifespan)

# The browser calls the API directly, so the Vercel origin must be allowed with cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CLIENT_ORIGIN", "http://localhost:3000" , "https://internship-project-ten-hazel.vercel.app/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOB_DIR = Path(tempfile.gettempdir()) / "brokerdesk"


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    # short message to the client, type only in the log: never message text or phones
    print(f"[api] unhandled {type(exc).__name__} on {request.url.path}", flush=True)
    return JSONResponse(status_code=500, content={"detail": "Server error. Try again."})


@app.get("/health")
def health() -> OkOut:
    return OkOut()


@app.get("/api/health")
def api_health() -> dict:
    return {"status": "ok", "db": db_ok()}


@app.post("/api/login")
def login(body: LoginBody, response: Response) -> LoginOut:
    if not check_password(body.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    set_session(response)
    # the client stores this and sends it as Authorization: Bearer
    return LoginOut(token=issue_token())


@app.get("/api/me")
def me(user: str = Depends(current_user)) -> MeOut:
    return MeOut(user=user)


@app.post("/api/logout")
def logout(response: Response) -> OkOut:
    clear_session(response)
    return OkOut()


def typed_reply(row: dict) -> str:
    if row["status"] != "saved":
        return f"{row['name'] or 'Ye customer'} pehle se hai."
    parts = [row["name"] or "Naya customer"]
    parts.append(row["locality"] or "locality nahi mili")
    if row["bhk"]:
        parts.append(f"{row['bhk']}bhk")
    parts.append(f"budget ₹{row['budget']:,}" if row["budget"] else "budget nahi mila")
    line = "✅ " + " — ".join(parts) + ". Customer add ho gaya."
    if row["phone"]:
        line += f" Phone: {row['phone']}."
    elif row.get("bad_phone"):
        line += f" Phone {row['bad_phone']} theek nahi laga — 10 digit likhein."
    else:
        line += " Phone nahi hai."
    return line


@app.post("/api/chat")
async def chat(body: ChatBody, user: str = Depends(current_user)) -> ChatOut:
    messages = [m.model_dump() for m in body.messages]
    # a lead typed by the broker becomes a customer row; questions fall through to chat
    try:
        typed = await run_in_threadpool(save_typed, messages[-1]["content"])
    except (RuntimeError, APIError, httpx.HTTPError):
        return ChatOut(reply="AI model se connect nahi ho paaya. GROQ_API_KEY check karein.")
    if typed:
        return ChatOut(reply=typed_reply(typed), href="/app/customers")
    return ChatOut(reply=await reply(messages))


@app.post("/api/voice")
def voice(file: UploadFile = File(...), user: str = Depends(current_user)) -> dict:
    data = file.file.read(MAX_AUDIO + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Audio file khali hai")
    try:
        return transcribe(data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        print("[voice] transcription failed", flush=True)
        raise HTTPException(status_code=500, detail="Voice note transcribe nahi ho paaya.")


@app.post("/api/ingest/zip", response_model=IngestOut)
def upload_zip(
    file: UploadFile = File(...),
    language: str = Form("hinglish"),
    user: str = Depends(current_user),
) -> IngestOut:
    # sync def on purpose: the LLM calls block, and FastAPI runs this in a threadpool
    data = file.file.read(MAX_ZIP + 1)
    if len(data) > MAX_ZIP:
        raise HTTPException(status_code=413, detail="ZIP is larger than 100 MB")

    job_id = uuid4().hex
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = JOB_DIR / f"{job_id}.zip"
    zip_path.write_bytes(data)

    try:
        with ingestion_graph() as graph:
            state = graph.invoke(
                {
                    "job_id": job_id,
                    "broker_id": BROKER_ID,
                    "zip_path": str(zip_path),
                    "language": "english" if language == "english" else "hinglish",
                    "files": [],
                    "candidates": [],
                    "transcripts": [],
                    "records": [],
                    "saved": [],
                    "needs_review": [],
                    "errors": [],
                    "counters": {},
                },
                {"configurable": {"thread_id": thread_id(job_id)}},
            )
    except (ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (APIError, httpx.HTTPError) as exc:
        print(f"[ingest] ai {type(exc).__name__}", flush=True)
        raise HTTPException(
            status_code=503,
            detail="AI model se connect nahi ho paaya. GROQ_API_KEY check karein.",
        ) from exc
    finally:
        # no resume endpoint exists, so every failed job used to leak the ZIP here
        zip_path.unlink(missing_ok=True)

    if not any(item["type"] != "ignored" for item in state.get("files", [])):
        raise HTTPException(status_code=400, detail="ZIP me koi .txt ya voice note nahi mila")

    counters = state.get("counters", {})
    return IngestOut(
        job_id=job_id,
        summary=state.get("summary", ""),
        chats_read=counters.get("chats_read", 0),
        candidates=counters.get("candidates", 0),
        customers_saved=counters.get("saved", 0),
        phone_missing=counters.get("phone_missing", 0),
        batches_retried=counters.get("batches_retried", 0),
        batches_skipped=counters.get("batches_skipped", 0),
    )


@app.get("/api/customers", response_model=list[CustomerOut])
def list_customers(
    locality: str | None = None,
    name: str | None = None,
    days: int | None = None,
    user: str = Depends(current_user),
) -> list[CustomerOut]:
    with Session() as session:
        query = select(Customer).where(Customer.broker_id == BROKER_ID)
        if locality:
            query = query.where(Customer.locality.ilike(f"%{locality}%"))
        if name:
            query = query.where(Customer.name.ilike(f"%{name}%"))
        if days:
            query = query.where(
                Customer.enquiry_date >= datetime.now(timezone.utc) - timedelta(days=days)
            )
        rows = session.scalars(
            query.order_by(Customer.enquiry_date.desc().nullslast(), Customer.id.desc())
        ).all()
        return [CustomerOut.model_validate(row) for row in rows]
