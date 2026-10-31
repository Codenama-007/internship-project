"""Groq chat model (hosted). The local Ollama version is kept below for offline work."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

# override=True: the values in server/.env win over any stale value already set in
# Windows. For production, set real environment variables on the host and this line
# can go back to the default (override=False).
load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def chat(**kwargs) -> ChatGroq:
    """One place the model is built, so extract.py and the chat share the config."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to server/.env (see .env.example).")
    # timeout 60s and 2 retries: a rate-limited call fails in about a minute instead of
    # hanging for minutes, so the upload does not look frozen.
    return ChatGroq(model=MODEL, api_key=key, timeout=60, max_retries=2, **kwargs)


# Local fallback, offline only: uncomment and drop GROQ_API_KEY.
# from langchain_ollama import ChatOllama
# llm = ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
#                  base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
#                  temperature=0.2, keep_alive="30m")

SYSTEM = (
    "You are BrokerDesk, an assistant for a rental property broker in Mumbai. "
    "Reply briefly, in the same language the broker uses (English or Hinglish). "
    "You have no property data yet: if asked about specific listings, appointments or "
    "brokerage, say the WhatsApp data is not connected yet instead of inventing numbers."
)


async def reply(messages: list[dict]) -> str:
    """Return the model's answer in one piece."""
    history = [SystemMessage(SYSTEM)] + [
        HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"])
        for m in messages
    ]
    try:
        return (await chat(temperature=0.2).ainvoke(history)).text
    except RuntimeError:
        # missing GROQ_API_KEY (raised by chat())
        print("[ai] GROQ_API_KEY is not set", flush=True)
        return "AI key set nahi hai. server/.env me GROQ_API_KEY add karein."
    except Exception as exc:
        # type only: never log message text or phone numbers
        print(f"[ai] chat failed: {type(exc).__name__}", flush=True)
        return "AI se connect nahi ho paaya. Server log dekhein."