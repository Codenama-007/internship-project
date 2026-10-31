from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginBody(BaseModel):
    password: str


class OkOut(BaseModel):
    ok: bool = True


class LoginOut(OkOut):
    # body token: the deployed client is on vercel.app and the API on onrender.com,
    # so a browser will not send the cross-site cookie on the next request.
    token: str


class MeOut(BaseModel):
    user: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatBody(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)


class ChatOut(BaseModel):
    reply: str
    href: str | None = None


class IngestOut(BaseModel):
    job_id: str
    summary: str
    chats_read: int
    candidates: int
    customers_saved: int
    phone_missing: int
    batches_retried: int
    batches_skipped: int


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    phone: str | None
    query_text: str
    locality: str | None
    bhk: str | None
    budget: int | None
    source: str
    source_chat: str
    enquiry_date: datetime | None
    created_at: datetime
