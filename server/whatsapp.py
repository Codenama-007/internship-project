"""WhatsApp export -> structured messages. No LLM here; pure parsing."""

import hashlib
import io
import os
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MAX_ZIP = 100 * 1024 * 1024
MAX_UNPACKED = 200 * 1024 * 1024

BROKER_ALIASES = [
    a.strip().lower() for a in os.getenv("BROKER_NAME", "Affan").split(",") if a.strip()
]

# Android: 12/31/23, 11:59 PM - Name: text        iOS: [31/12/23, 23:59:00] Name: text
ANDROID = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*([AaPp])?\.?[Mm]?\.?\s+-\s+([^:\n]{1,60}?):\s(.*)$"
)
IOS = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*([AaPp][Mm])?\]\s+([^:\n]{1,60}?):\s(.*)$"
)
# timestamp with no sender = system notice ("You created group ...", encryption line)
SYSTEM_LINE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*([AaPp])?\.?[Mm]?\.?\s+-\s+(.*)$"
)
PHONE = re.compile(r"^\+?[\d][\d\s\-()]{6,}$")

MEDIA = (
    "<media omitted>",
    "image omitted",
    "video omitted",
    "audio omitted",
    "document omitted",
    "sticker omitted",
    "gif omitted",
    "contact card omitted",
)


@dataclass
class Message:
    sender: str
    text: str
    when: datetime | None
    digest: str


@dataclass
class Chat:
    source: str
    title: str
    messages: list[Message] = field(default_factory=list)

    @property
    def senders(self) -> list[str]:
        seen: dict[str, None] = {}
        for m in self.messages:
            if m.sender.lower() not in BROKER_ALIASES:
                seen.setdefault(m.sender, None)
        return list(seen)

    @property
    def is_group(self) -> bool:
        return len({m.sender.lower() for m in self.messages}) > 2


def _parse_when(date_s: str, time_s: str, ampm: str | None) -> datetime | None:
    a, b, y = (int(x) for x in date_s.split("/"))
    # shortcut: dd/mm assumed unless impossible (India default); upgrade: read the device locale
    day, month = (a, b) if a > 12 or b <= 12 else (b, a)
    year = y + 2000 if y < 100 else y
    hh, mm, *rest = (int(x) for x in time_s.split(":"))
    ss = rest[0] if rest else 0
    if ampm:
        hh %= 12
        if ampm.lower() == "p":
            hh += 12
    try:
        return datetime(year, month, day, hh, mm, ss)
    except ValueError:
        return None


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def parse_txt(text: str, source: str, title: str) -> Chat:
    chat = Chat(source=source, title=title)
    for raw in text.splitlines():
        # iOS puts thin/narrow no-break spaces around times and invisible direction marks
        line = raw.replace("\u202f", " ").replace("\u200e", "").rstrip()
        if not line:
            continue

        match = ANDROID.match(line) or IOS.match(line)
        if match:
            date_s, time_s, ampm, sender, body = match.groups()
            if body.strip().lower() in MEDIA:
                continue
            chat.messages.append(
                Message(
                    sender=sender.strip(),
                    text=body.strip(),
                    when=_parse_when(date_s, time_s, ampm),
                    digest=hashlib.sha1(
                        f"{source}|{date_s} {time_s}|{sender}|{body}".encode()
                    ).hexdigest(),
                )
            )
            continue

        if SYSTEM_LINE.match(line):
            continue  # "Messages are end-to-end encrypted", "created group", etc.

        if chat.messages:  # multi-line message
            last = chat.messages[-1]
            last.text += "\n" + line
            # fold into the previous digest: hashing the bare line let two chats with the
            # same continuation line collide and silently drop a lead
            last.digest = hashlib.sha1(f"{last.digest}|{line}".encode()).hexdigest()
    return chat


def parse_zip(data: bytes) -> list[Chat]:
    if len(data) > MAX_ZIP:
        raise ValueError("ZIP is larger than 100 MB")

    chats: list[Chat] = []
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if sum(i.file_size for i in zf.infolist()) > MAX_UNPACKED:
            raise ValueError("Unpacked files are too large")
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in name.split("/"):
                raise ValueError(f"Unsafe path in ZIP: {name}")
            if not name.lower().endswith(".txt"):
                continue
            title = name.rsplit("/", 1)[-1]
            for prefix in ("WhatsApp Chat with ", "WhatsApp Chat - "):
                if title.startswith(prefix):
                    title = title[len(prefix) :]
            if title.lower().endswith(".txt"):
                title = title[:-4]
            chat = parse_txt(_decode(zf.read(info)), source=name, title=title)
            if chat.messages:
                chats.append(chat)
    return chats


def candidates(chats: list[Chat]) -> list[dict]:
    """Non-broker messages, grouped per sender — what the LLM will read."""
    out: list[dict] = []
    for chat in chats:
        for sender in chat.senders:
            msgs = [m for m in chat.messages if m.sender == sender]
            out.append(
                {
                    "chat": chat.source,
                    "title": chat.title,
                    "group": chat.is_group,
                    "sender": sender,
                    "messages": [
                        {
                            "text": m.text,
                            "when": m.when.isoformat() if m.when else None,
                            "hash": m.digest,
                        }
                        for m in msgs
                    ],
                }
            )
    return out


def phone_of(sender: str) -> str | None:
    if PHONE.match(sender):
        digits = re.sub(r"\D", "", sender)
        return digits if len(digits) >= 7 else None
    return None
