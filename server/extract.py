"""WhatsApp candidates -> rental leads. LLM classifies and extracts, Python decides numbers."""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from llm import chat
from whatsapp import phone_of

PROMPT = """You classify ONE WhatsApp contact of a Mumbai rental broker.

Question: is this person ASKING for a flat to rent (tenant), or OFFERING a flat (owner, landlord, broker posting a listing)?

is_lead is true ONLY when the person asks for a flat: "chahiye", "looking for", "need", "dikhana hai", "dekhna hai", "on rent".
is_lead is false when the person offers a flat: "available hai", "khali ho gaya hai", "rent 48000", "owner contact", or when they only greet, thank or chat.

Examples:
["bhai Andheri me 2bhk chahiye 45k tak"] -> {"is_lead": true, "name": null, "locality": "Andheri West", "bhk": "2", "budget_text": "45k", "query_text": "2bhk Andheri West 45k"}
["2 BHK available in Lokhandwala, 55,000 rent, semi furnished. Owner contact: 98200 99887"] -> {"is_lead": false, "name": null, "locality": null, "bhk": null, "budget_text": null, "query_text": null}
["Affan, mera 2bhk Versova me khali ho gaya hai", "Rent 48000, deposit 3 month"] -> {"is_lead": false, "name": null, "locality": null, "bhk": null, "budget_text": null, "query_text": null}

Rules for the fields when is_lead is true:
- name: the name stated in a message ("Mera naam Rohit Mehta hai", "this is Karan Desai", "Call me - Vikram"), else the contact_name if it is not a phone number, else null. contact_name is the group name in a group chat, never a person.
- Never use a phone number written inside a message body.
- locality: the area they name (Andheri West, Lokhandwala, Powai, Versova). null if not stated.
- bhk: "1", "2", "3", "1 RK". null if not stated.
- budget_text: copy their exact words about rent or budget, character for character. "25 hazaar" stays "25 hazaar", never "25 lakh". If they correct themselves, keep the whole correction.
- query_text: one short Hinglish line saying what they want.
- Never invent a value. Unknown is null.

Reply with the JSON object only."""

def _ask(payload: dict) -> dict | None:
    """One candidate in, one JSON object out. None means the model broke the contract."""
    raw = chat(
        temperature=0,
        # gpt-oss spends tokens on reasoning; 300 left no room for the JSON and Groq
        # rejected every call with json_validate_failed.
        max_tokens=1500,
        model_kwargs={"response_format": {"type": "json_object"}},
    ).invoke(
        [SystemMessage(PROMPT), HumanMessage(json.dumps(payload, ensure_ascii=False))]
    ).text
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("is_lead"), bool):
        return None
    return data


def extract(cands: list[dict], log=print) -> tuple[list[dict], int, int]:
    """Candidate per LLM call: a 4-candidate batch made llama3.2:3b drop 3 of 4 leads.

    Returns (results, batches_retried, batches_skipped). A batch is one candidate.
    """
    results: list[dict] = []
    retried = skipped = 0

    for number, cand in enumerate(cands, 1):
        payload = {
            "sender": cand["sender"],
            "contact_name": cand["title"],
            "group": cand["group"],
            "messages": [m["text"] for m in cand["messages"]],
        }
        data = _ask(payload)
        if data is None:
            retried += 1
            data = _ask(payload)

        log(f"\n--- batch {number}/{len(cands)}: {cand['sender']} ---")
        if data is None:
            skipped += 1
            log("invalid JSON twice -> batch skipped")
            continue
        log(json.dumps(data, ensure_ascii=False))
        if data["is_lead"] and is_listing(cand):
            data["is_lead"] = False
            log("python veto: the messages offer a flat, not ask for one")
        results.append({"cand": cand, "data": data})

    return results, retried, skipped


OFFER = ("available", "khali", "owner contact", "deposit", "for rent")
ASK = (
    "chahiye",
    "chahiya",
    "looking for",
    "need",
    "dikhana",
    "dekhna",
    "dekhne",
    "on rent",
    "budget",
    "requirement",
    "shift",
)


def is_listing(cand: dict) -> bool:
    """Veto only: turn an LLM 'lead' off when the words are an offer. Never creates a lead.

    shortcut: keyword veto tuned on the fixture; upgrade: embedding check against the
    listing examples if real exports start slipping through.
    """
    text = " ".join(m["text"] for m in cand["messages"]).lower()
    return any(w in text for w in OFFER) and not any(w in text for w in ASK)


BUDGET = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(k|thousand|hazaar|hazar|lakh|lakhs|lac|lacs|l|cr|crore)?",
    re.I,
)
THOUSANDS = {"k", "thousand", "hazaar", "hazar"}
LAKHS = {"lakh", "lakhs", "lac", "lacs", "l"}


def parse_budget(text: str | None) -> int | None:
    """'45k' -> 45000, '1.2L' -> 120000, '25 hazaar' -> 25000, '32,000' -> 32000.

    Last mention wins so a correction ("1.2L ... I meant 38000") resolves to 38000.
    Anything outside a plausible Mumbai monthly rent is ignored, so '3bhk' and
    'deposit 3 month' cannot become a budget.
    """
    if not text:
        return None
    for match in reversed(list(BUDGET.finditer(text))):
        unit = (match.group(2) or "").lower()
        try:
            value = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        if unit in THOUSANDS:
            value *= 1_000
        elif unit in LAKHS:
            value *= 100_000
        elif unit in {"cr", "crore"}:
            value *= 10_000_000
        value = int(round(value))
        if 2_000 <= value <= 5_000_000:
            return value
    return None


def normalize_bhk(value: str | None) -> str | None:
    """'1bhk' -> '1', '1 RK' -> '1' (the key stores the count; 'RK' stays in query_text)."""
    if not value:
        return None
    digits = re.search(r"\d+", str(value))
    return digits.group() if digits else None


def lead_name(data: dict, cand: dict) -> str | None:
    name = (data.get("name") or "").strip() or None
    if name and cand["group"] and name.lower() == (cand["title"] or "").lower():
        name = None  # small models copy the group subject as the person's name
    if not name and not phone_of(cand["sender"]):
        name = cand["sender"]
    return name
