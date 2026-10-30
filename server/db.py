import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# absolute path: works whatever folder uvicorn is started from
load_dotenv(Path(__file__).resolve().parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Add it to server/.env (see .env.example)."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)

# shortcut: one broker per install, so every customer is broker_id 1; upgrade: real
# accounts table + broker_id taken from the session when a second broker signs up.
BROKER_ID = 1


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    broker_id: Mapped[int] = mapped_column(Integer, index=True, default=BROKER_ID)
    name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20), index=True)
    query_text: Mapped[str] = mapped_column(String(2000))
    locality: Mapped[str | None] = mapped_column(String(80), index=True)
    bhk: Mapped[str | None] = mapped_column(String(20))
    budget: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(200), default="text")
    source_chat: Mapped[str] = mapped_column(String(200))
    enquiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_msg_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AgentLog(Base):
    """One row per node run. Counts only: never message text or phone numbers."""

    __tablename__ = "agent_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), index=True)
    node: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    counts: Mapped[dict | None] = mapped_column(JSON)
