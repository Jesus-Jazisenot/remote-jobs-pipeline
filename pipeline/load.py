"""LOAD — copy every landed JSONL file into DuckDB raw tables (raw.<source>).

Schemas drift between runs (APIs add or drop fields), so files are read with
union_by_name and the raw table is rebuilt from the full landing zone each time.
That keeps loads idempotent: running twice gives the same result.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "warehouse.duckdb"


def run(raw_dir: Path | None = None, db_path: Path | None = None) -> dict[str, int]:
    raw_dir = raw_dir or Path(os.environ.get("RAW_DIR", ROOT / "data" / "raw"))
    db_path = db_path or Path(os.environ.get("DUCKDB_PATH", DEFAULT_DB))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    counts = {}
    with duckdb.connect(str(db_path)) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        for source_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
            files = sorted(source_dir.glob("*.jsonl"))
            if not files:
                continue
            glob = (source_dir / "*.jsonl").as_posix()
            con.execute(
                f"""CREATE OR REPLACE TABLE raw.{source_dir.name} AS
                    SELECT *
                    FROM read_json_auto(?, format='newline_delimited', union_by_name=true,
                                        filename=true, sample_size=-1)""",
                [glob],
            )
            n = con.execute(f"SELECT count(*) FROM raw.{source_dir.name}").fetchone()[0]
            counts[source_dir.name] = n
            print(f"+ raw.{source_dir.name}: {n} rows from {len(files)} file(s)")
    return counts


if __name__ == "__main__":
    run()
