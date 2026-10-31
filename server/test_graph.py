"""Run: server/.venv/Scripts/python.exe server/test_graph.py

1. prints the file-type route for the fixture ZIP
2. full run: must store exactly the 6 customers from EXPECTED_LEADS.md
3. interrupted run: stops after text_tool, reloads the checkpoint in a new connection,
   finishes, and must store exactly the same 6 customers without re-saving.
"""

import os
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/brokerdesk_test",
)

from sqlalchemy import func, select  # noqa: E402

from db import AgentLog, Base, Customer, Session, engine  # noqa: E402
from graph import ingestion_graph, route_after_unpack, thread_id  # noqa: E402
from nodes import unpack_zip  # noqa: E402

ZIP = HERE / "fixtures" / "whatsapp_fake_export.zip"
STAGE = Path(tempfile.gettempdir()) / "brokerdesk-tests"

# fresh_db() drops every table: never let this script point at a real database
assert (engine.url.database or "").endswith("_test"), f"refusing to touch {engine.url.database}"

# name -> (phone, locality, bhk, budget) from EXPECTED_LEADS.md
EXPECTED = {
    "Rohit Mehta": ("919820011223", "Andheri West", "2", 45000),
    "Karan Desai": ("917738022145", "Lokhandwala", "1", 32000),
    "Ramesh Bhai": (None, "Versova", "1", 25000),
    "Vikram": ("919833477001", "Andheri East", "2", 50000),
    "Sneha Kulkarni": (None, "Andheri West", "1", 38000),
    "Imran Sheikh": (None, "Powai", "3", 90000),
}


def fresh_db() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def stage(job_id: str) -> Path:
    STAGE.mkdir(parents=True, exist_ok=True)
    path = STAGE / f"{job_id}.zip"
    shutil.copy(ZIP, path)
    return path


def initial(job_id: str, path: Path) -> dict:
    return {
        "job_id": job_id,
        "broker_id": 1,
        "zip_path": str(path),
        "language": "hinglish",
        "files": [],
        "candidates": [],
        "transcripts": [],
        "records": [],
        "saved": [],
        "needs_review": [],
        "errors": [],
        "counters": {},
    }


def rows() -> list[Customer]:
    with Session() as session:
        return list(session.scalars(select(Customer).order_by(Customer.id)))


def snapshot(saved: list[Customer]) -> list[tuple]:
    return [(r.name, r.phone, r.locality, r.bhk, r.budget) for r in saved]


def check_customers(saved: list[Customer]) -> None:
    assert len(saved) == 6, f"expected 6 customers, stored {len(saved)}"
    by_name = {row.name: row for row in saved}
    assert set(by_name) == set(EXPECTED), f"names differ: {sorted(by_name)}"

    for name, (phone, locality, bhk, budget) in EXPECTED.items():
        row = by_name[name]
        assert row.phone == phone, f"{name} phone {row.phone!r} != {phone!r}"
        assert row.locality == locality, f"{name} locality {row.locality!r}"
        assert row.bhk == bhk, f"{name} bhk {row.bhk!r}"
        assert row.budget == budget, f"{name} budget {row.budget!r} != {budget}"
        assert row.source == "text", f"{name} source {row.source!r}"
        assert row.query_text, f"{name} has no query_text"

    assert sum(1 for row in saved if row.phone is None) == 3, "expected 3 phone-less"
    for phone in ("919820011223", "919833477001"):
        assert sum(1 for r in saved if r.phone == phone) == 1, f"{phone} was not merged"
    assert all(r.phone != "919004066218" for r in saved), "group listing became a customer"
    assert all("sharma" not in (r.name or "").lower() for r in saved), "landlord stored"


def check_summary(state: dict) -> None:
    counters = state["counters"]
    assert counters["chats_read"] == 5, counters
    assert counters["candidates"] == 8, counters
    assert counters["saved"] == 6, counters
    assert counters["phone_missing"] == 3, counters
    assert counters["batches_skipped"] == 0, counters


def main() -> None:
    # 1) route chosen for the fixture
    path = stage("route")
    files = unpack_zip({"job_id": "route", "zip_path": str(path)})["files"]
    print("=== file types ===")
    for item in files:
        print(f"  {item['type']:<8} {item['path']}")
    route = route_after_unpack({"files": files})
    print(f"=== route chosen: {route} ===\n")
    assert route == "text", route

    # 2) uninterrupted run
    fresh_db()
    with ingestion_graph() as graph:
        full = graph.invoke(
            initial("job-full", path), {"configurable": {"thread_id": thread_id("job-full")}}
        )
    print("=== uninterrupted run ===")
    print("summary:", full["summary"], "| counters:", full["counters"])
    check_summary(full)
    reference = snapshot(rows())
    check_customers(rows())

    # 3) interrupted run: stop after text_tool, reload the checkpoint, finish
    fresh_db()
    with ingestion_graph(interrupt_after=["text_tool"]) as graph:
        paused = graph.invoke(
            initial("job-resume", path),
            {"configurable": {"thread_id": thread_id("job-resume")}},
        )
    print("\n=== paused after text_tool ===")
    print("records extracted:", len(paused.get("records", [])), "| stored:", len(rows()))
    assert paused.get("records"), "text_tool produced no records"
    assert len(rows()) == 0, "save_customer must not run before the pause"

    # new connection = fresh process, resuming the same thread
    with ingestion_graph() as graph:
        resumed = graph.invoke(
            None, {"configurable": {"thread_id": thread_id("job-resume")}}
        )
    print("resumed summary:", resumed["summary"], "| counters:", resumed["counters"])
    check_summary(resumed)
    check_customers(rows())
    assert snapshot(rows()) == reference, "resumed run differs from the uninterrupted run"

    with Session() as session:
        logged = session.scalar(
            select(func.count()).select_from(AgentLog).where(
                AgentLog.job_id == "job-resume"
            )
        )
    print(f"agent_log rows for job-resume: {logged}")
    assert logged and logged >= 5, logged

    print("\n=== stored customers ===")
    for row in rows():
        print(
            f"{row.id} | {row.name or '-':<15} | {row.phone or '(missing)':<14} | "
            f"{row.locality or '-':<13} | {row.bhk or '-':<4} | {row.budget or '-':<6} | "
            f"{row.source:<6} | {row.source_chat}"
        )
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
