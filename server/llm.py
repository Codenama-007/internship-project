import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

load_dotenv(Path(__file__).resolve().parent / ".env")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

SYSTEM = (
    "You are BrokerDesk, an assistant for a rental property broker in Mumbai. "
    "Reply briefly, in the same language the broker uses (English or Hinglish). "
    "You have no property data yet: if asked about specific listings, appointments or "
    "brokerage, say the WhatsApp data is not connected yet instead of inventing numbers."
)

llm = ChatOllama(
    model=MODEL,
    base_url=OLLAMA_URL,
    temperature=0.2,
    # keep the 3B model resident: a cold reload on this machine took 50-110s
    keep_alive="30m",
)


async def reply(messages: list[dict]) -> str:
    """Return the model's answer in one piece."""
    history = [SystemMessage(SYSTEM)] + [
        HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"])
        for m in messages
    ]
    try:
        # ainvoke, not invoke: invoke blocks the event loop for every other request
        return (await llm.ainvoke(history)).text
    except Exception:
        # shortcut: whole answer or nothing — no token streaming. Upgrade: astream +
        # StreamingResponse if time-to-first-token ever matters.
        return "Ollama is not reachable. Start it with `ollama serve`, then pull a model if needed."
