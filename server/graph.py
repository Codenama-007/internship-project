"""One StateGraph, deterministic routing. The LLM never picks a route or writes a row."""

from contextlib import contextmanager

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from db import DATABASE_URL
from nodes import (
    audio_tool,
    logged,
    normalize_record,
    save_customer,
    summarize,
    text_tool,
    unpack_zip,
)
from state import IngestState

CONNINFO = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)


def route_after_unpack(state: IngestState) -> str:
    kinds = {item["type"] for item in state.get("files", [])}
    if "text" in kinds:
        return "text"
    return "audio" if "audio" in kinds else "none"


def route_after_text(state: IngestState) -> str:
    return "audio" if any(f["type"] == "audio" for f in state.get("files", [])) else "done"


def build() -> StateGraph:
    graph = StateGraph(IngestState)
    graph.add_node("unpack_zip", logged("unpack_zip", unpack_zip))
    graph.add_node("text_tool", logged("text_tool", text_tool))
    graph.add_node("audio_tool", logged("audio_tool", audio_tool))
    graph.add_node("normalize_record", logged("normalize_record", normalize_record))
    graph.add_node("save_customer", logged("save_customer", save_customer))
    graph.add_node("summarize", logged("summarize", summarize))

    graph.add_edge(START, "unpack_zip")
    graph.add_conditional_edges(
        "unpack_zip",
        route_after_unpack,
        {"text": "text_tool", "audio": "audio_tool", "none": "summarize"},
    )
    graph.add_conditional_edges(
        "text_tool", route_after_text, {"audio": "audio_tool", "done": "normalize_record"}
    )
    graph.add_edge("audio_tool", "normalize_record")
    graph.add_edge("normalize_record", "save_customer")
    graph.add_edge("save_customer", "summarize")
    graph.add_edge("summarize", END)
    return graph


def compile_graph(checkpointer=None, interrupt_after=None):
    return build().compile(checkpointer=checkpointer, interrupt_after=interrupt_after)


@contextmanager
def ingestion_graph(interrupt_after: list[str] | None = None):
    with PostgresSaver.from_conn_string(CONNINFO) as saver:
        saver.setup()
        yield compile_graph(saver, interrupt_after)


def thread_id(job_id: str) -> str:
    return f"ingest-{job_id}"
