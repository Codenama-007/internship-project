"""The graph's only memory. Every node returns just the keys it changes."""

from typing import Literal, TypedDict

FileType = Literal["text", "audio", "ignored"]


class FileItem(TypedDict):
    path: str
    type: FileType
    chat_name: str | None


class Message(TypedDict):
    text: str
    when: str | None
    hash: str


class Candidate(TypedDict):
    chat: str
    title: str
    group: bool
    sender: str
    messages: list[Message]


class Transcript(TypedDict):
    file: str
    text: str
    language: str | None


class Record(TypedDict, total=False):
    name: str | None
    phone: str | None
    query_text: str
    locality: str | None
    bhk: str | None
    budget_raw: str | None
    budget: int | None
    source: str
    source_chat: str
    enquiry_date: str | None
    source_msg_hash: str
    confidence: float | None


class Counters(TypedDict, total=False):
    chats_read: int
    candidates: int
    saved: int
    phone_missing: int
    batches_retried: int
    batches_skipped: int


class IngestState(TypedDict, total=False):
    job_id: str
    broker_id: int
    zip_path: str
    language: Literal["hinglish", "english"]
    files: list[FileItem]
    candidates: list[Candidate]
    transcripts: list[Transcript]
    records: list[Record]
    saved: list[dict]
    needs_review: list[dict]
    errors: list[str]
    counters: Counters
    summary: str
