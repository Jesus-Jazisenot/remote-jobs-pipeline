"""EXTRACT — pull raw job postings from three public APIs and land them untouched.

The landing zone is append-only JSON Lines, one file per source per run:

    data/raw/<source>/<YYYY-MM-DD>.jsonl

Nothing is cleaned here on purpose (ELT, not ETL): if a transformation has a bug,
dbt can be re-run over the original payloads without calling the APIs again.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
HEADERS = {"User-Agent": "remote-jobs-pipeline/1.0 (portfolio project; github.com/Jesus-Jazisenot)"}

HIMALAYAS_QUERIES = [
    "python", "web scraping", "automation", "ai engineer", "llm", "chatbot", "full stack",
    "next.js", "backend", "data engineer", "integration engineer", "junior developer",
]
REMOTIVE_CATEGORIES = ["software-dev", "data", "devops", "all-others"]


def _get(url: str):
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def himalayas(pages: int = 3) -> list[dict]:
    out = []
    for q in HIMALAYAS_QUERIES:
        for page in range(1, pages + 1):
            url = f"https://himalayas.app/jobs/api/search?q={urllib.parse.quote(q)}&page={page}"
            jobs = _get(url).get("jobs", [])
            out += [{**j, "_query": q} for j in jobs]
            if len(jobs) < 15:
                break
            time.sleep(0.5)  # be polite
    return out


def remotive() -> list[dict]:
    out = []
    for cat in REMOTIVE_CATEGORIES:
        jobs = _get(f"https://remotive.com/api/remote-jobs?category={cat}").get("jobs", [])
        out += [{**j, "_query": cat} for j in jobs]
    return out


def remoteok() -> list[dict]:
    return _get("https://remoteok.com/api")[1:]  # element 0 is a legal notice


SOURCES = {"himalayas": himalayas, "remotive": remotive, "remoteok": remoteok}


def run(run_date: str | None = None) -> dict[str, int]:
    run_date = run_date or datetime.now(UTC).date().isoformat()
    fetched_at = datetime.now(UTC).isoformat(timespec="seconds")
    counts = {}
    for name, fetch in SOURCES.items():
        try:
            rows = fetch()
        except Exception as e:  # one source down must not kill the whole run
            print(f"! {name}: {e}")
            counts[name] = 0
            continue
        path = RAW / name / f"{run_date}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps({**row, "_fetched_at": fetched_at}, ensure_ascii=False) + "\n")
        counts[name] = len(rows)
        print(f"+ {name}: {len(rows)} postings -> {path.relative_to(RAW.parent.parent)}")
    return counts


if __name__ == "__main__":
    run()
