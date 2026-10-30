"""Graph nodes. Only save_customer touches the database; only text_tool calls the LLM."""

import hashlib
import io
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db import BROKER_ID, AgentLog, Customer, Session
from extract import extract, is_listing, lead_name, normalize_bhk, parse_budget
from state import IngestState
from whatsapp import MAX_UNPACKED, MAX_ZIP, candidates, parse_zip, phone_of

AUDIO_EXT = {".opus", ".m4a", ".mp3", ".ogg", ".wav", ".aac", ".webm"}


def logged(name: str, node):
    """Record one agent_log row per node run: counts only, never text or phones."""

    def run(state: IngestState) -> dict:
        started = datetime.now(timezone.utc)
        result = node(state)
        counts = {k: len(v) for k, v in result.items() if isinstance(v, list)}
        if "counters" in result:
            counts.update(result["counters"])
        try:
            with Session() as session:
                session.add(
                    AgentLog(
                        job_id=state.get("job_id", ""),
                        node=name,
                        started_at=started,
                        finished_at=datetime.now(timezone.utc),
                        counts=counts or None,
                    )
                )
                session.commit()
        except Exception:
            pass  # logging must never fail an ingest
        return result

    run.__name__ = name
    return run


def chat_title(path: str) -> str:
    title = path.rsplit("/", 1)[-1]
    for prefix in ("WhatsApp Chat with ", "WhatsApp Chat - "):
        if title.startswith(prefix):
            title = title[len(prefix) :]
    return title[:-4] if title.lower().endswith(".txt") else title


def unpack_zip(state: IngestState) -> dict:
    data = Path(state["zip_path"]).read_bytes()
    if len(data) > MAX_ZIP:
        raise ValueError("ZIP is larger than 100 MB")

    files = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(item.file_size for item in archive.infolist()) > MAX_UNPACKED:
            raise ValueError("Unpacked files are too large")
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = info.filename.replace("\\", "/")
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError(f"Unsafe path in ZIP: {path}")
            suffix = Path(path).suffix.lower()
            kind = (
                "text"
                if suffix == ".txt"
                else "audio"
                if suffix in AUDIO_EXT
                else "ignored"
            )
            files.append(
                {
                    "path": path,
                    "type": kind,
                    "chat_name": chat_title(path) if kind != "ignored" else None,
                }
            )
    return {"files": files}


def text_tool(state: IngestState) -> dict:
    chats = parse_zip(Path(state["zip_path"]).read_bytes())
    found = candidates(chats)
    results, retried, skipped = extract(found)

    records = [rec for item in results if (rec := _record(item["cand"], item["data"]))]
    return {
        "candidates": found,
        "records": list(state.get("records", [])) + records,
        "counters": {
            **state.get("counters", {}),
            "chats_read": len(chats),
            "candidates": len(found),
            "batches_retried": retried,
            "batches_skipped": skipped,
        },
    }


def _record(cand: dict, data: dict) -> dict | None:
    if not data.get("is_lead"):
        return None
    first = cand["messages"][0]
    return {
        "name": lead_name(data, cand),
        "phone": phone_of(cand["sender"]),
        "query_text": (data.get("query_text") or first["text"])[:2000],
        "locality": (data.get("locality") or "").strip() or None,
        "bhk": data.get("bhk"),
        "budget_raw": data.get("budget_text"),
        "budget": None,
        "source": "text",
        "source_chat": cand["title"],
        "enquiry_date": first["when"],
        "source_msg_hash": first["hash"],
        "confidence": data.get("confidence"),
    }


LEAD_HINT = re.compile(
    r"\b(bhk|rk|flat|apartment|budget|chahiye|chahiya|dekhna|dikhana|dekhne|rent|kiraya)\b",
    re.I,
)
MOBILE = re.compile(r"(?<!\d)(\d{10,13})(?!\d)")


def save_typed(text: str) -> dict | None:
    """A lead the broker types in chat -> one customer row. None when it is not a lead.

    shortcut: same extract() prompt as WhatsApp, so a question that sounds like a request
    ("mujhe 2bhk chahiye?") can be saved as a customer. Upgrade: a confirm step in the UI.
    """
    if not LEAD_HINT.search(text):
        return None
    clean = text.strip()
    when = datetime.now(timezone.utc).isoformat()
    cand = {
        "chat": "manual",
        "title": "Added from chat",
        "group": False,
        "sender": "",
        "messages": [
            {
                "text": clean,
                "when": when,
                "hash": hashlib.sha256(clean.lower().encode()).hexdigest(),
            }
        ],
    }
    results, _, _ = extract([cand])
    if not results:
        return None
    data = results[0]["data"]
    # the broker typed "add ...", so is_lead from the 3B model is not trusted here;
    # any extracted field is enough. The listing veto still applies.
    if is_listing(cand) or not any(
        data.get(key) for key in ("name", "locality", "bhk", "budget_text")
    ):
        return None
    # _record() ignores non-leads; for typed input the broker already said "add"
    record = _record(cand, {**data, "is_lead": True})
    if not record:
        return None
    # no WhatsApp sender here, so a number typed in the message is the customer's own
    phone_raw = MOBILE.search(clean)
    digits = phone_raw.group(1) if phone_raw else ""
    bad_phone = None
    if len(digits) == 10 and digits[0] in "6789":
        record["phone"] = "91" + digits
    elif len(digits) == 12 and digits.startswith("91"):
        record["phone"] = digits
    else:
        record["phone"] = None
        bad_phone = digits or None
    record["source"] = "manual"
    normalized = normalize_record({"records": [record]})["records"][0]
    result = save_customer({"records": [normalized], "counters": {}})
    status = result["saved"][0]["status"] if result["saved"] else "duplicate"
    return {
        "status": status,
        "name": normalized.get("name"),
        "locality": normalized.get("locality"),
        "bhk": normalized.get("bhk"),
        "budget": normalized.get("budget"),
        "phone": normalized.get("phone"),
        "bad_phone": bad_phone,
    }


def audio_tool(state: IngestState) -> dict:
    """Step 5 replaces this with faster-whisper. Until then the files are held for review."""
    review = list(state.get("needs_review", []))
    for item in state.get("files", []):
        if item["type"] == "audio":
            review.append(
                {"file": item["path"], "reason": "voice notes not transcribed yet"}
            )
    return {"needs_review": review}


def normalize_record(state: IngestState) -> dict:
    normalized = []
    for record in state.get("records", []):
        record = dict(record)
        record["budget"] = parse_budget(record.get("budget_raw")) or parse_budget(
            record.get("query_text")
        )
        record["bhk"] = normalize_bhk(record.get("bhk"))
        record["phone"] = re.sub(r"\D", "", record["phone"]) if record.get("phone") else None
        locality = (record.get("locality") or "").strip()
        # title-case only lowercase input so "andheri west" -> "Andheri West" but BKC stays BKC
        record["locality"] = (locality.title() if locality.islower() else locality) or None
        normalized.append(record)
    return {"records": normalized}


def save_customer(state: IngestState) -> dict:
    saved: list[dict] = []
    written: list[dict] = []
    counters = dict(state.get("counters", {}))

    with Session() as session:
        known = set(
            session.scalars(
                select(Customer.source_msg_hash).where(Customer.broker_id == BROKER_ID)
            )
        )
        for record in state.get("records", []):
            brief = {
                "name": record.get("name"),
                "locality": record.get("locality"),
                "status": "saved",
            }
            if record["source_msg_hash"] in known:
                saved.append({**brief, "status": "duplicate"})
                continue

            # same phone (or same name when there is no phone) + same locality = one person
            duplicate = None
            if record.get("phone") or record.get("name"):
                key = (
                    Customer.phone == record["phone"]
                    if record.get("phone")
                    else Customer.name == record["name"]
                )
                duplicate = session.scalars(
                    select(Customer).where(
                        Customer.broker_id == BROKER_ID,
                        Customer.locality == record.get("locality"),
                        key,
                    )
                ).first()
            if duplicate:
                saved.append({**brief, "status": "merged"})
                continue

            inserted = session.execute(
                pg_insert(Customer)
                .values(
                    broker_id=BROKER_ID,
                    name=record.get("name"),
                    phone=record.get("phone"),
                    query_text=record["query_text"],
                    locality=record.get("locality"),
                    bhk=record.get("bhk"),
                    budget=record.get("budget"),
                    source=record.get("source", "text"),
                    source_chat=record["source_chat"],
                    enquiry_date=(
                        datetime.fromisoformat(record["enquiry_date"])
                        if record.get("enquiry_date")
                        else None
                    ),
                    source_msg_hash=record["source_msg_hash"],
                )
                .on_conflict_do_nothing(index_elements=["source_msg_hash"])
            ).rowcount
            if inserted:
                saved.append(brief)
                written.append(record)
            else:
                saved.append({**brief, "status": "duplicate"})

        session.commit()

    counters.update(
        saved=len(written),
        phone_missing=sum(1 for record in written if record.get("phone") is None),
    )
    return {"saved": saved, "counters": counters}


ENGLISH = (
    "Read {chats_read} chats, found {candidates} people. "
    "{saved} customers saved ({phone_missing} without a phone), "
    "{batches_retried} batches retried, {batches_skipped} batches skipped."
)
HINGLISH = (
    "{chats_read} chats padhi, {candidates} log mile. "
    "{saved} customers save hue ({phone_missing} ka phone nahi hai), "
    "{batches_retried} batch retry, {batches_skipped} batch skip."
)


def summarize(state: IngestState) -> dict:
    counters = state.get("counters", {})
    template = ENGLISH if state.get("language") == "english" else HINGLISH
    summary = template.format(
        chats_read=counters.get("chats_read", 0),
        candidates=counters.get("candidates", 0),
        saved=counters.get("saved", 0),
        phone_missing=counters.get("phone_missing", 0),
        batches_retried=counters.get("batches_retried", 0),
        batches_skipped=counters.get("batches_skipped", 0),
    )
    if state.get("needs_review"):
        summary += f" {len(state['needs_review'])} file(s) need a look."
    return {"summary": summary}
