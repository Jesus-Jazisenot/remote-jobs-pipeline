"""Run the whole pipeline: extract → load → dbt build (models + tests) → report.

    python -m pipeline.run                # live APIs
    python -m pipeline.run --fixtures     # offline, with the sample payloads in tests/fixtures
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from pipeline import extract, load, report

ROOT = Path(__file__).resolve().parents[1]


def dbt_build() -> None:
    dbt = Path(sys.executable).with_name("dbt.exe" if os.name == "nt" else "dbt")
    cmd = [str(dbt), "build", "--project-dir", "transform", "--profiles-dir", "transform"]
    # A failing data test stops the run here, so a broken page is never published.
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", action="store_true", help="skip the APIs, use tests/fixtures")
    args = ap.parse_args()

    if args.fixtures:
        os.environ["RAW_DIR"] = str(ROOT / "tests" / "fixtures" / "raw")
        os.environ.setdefault("DUCKDB_PATH", str(ROOT / "data" / "fixtures.duckdb"))
        os.environ.setdefault("REPORT_PATH", str(ROOT / "data" / "fixtures_report.html"))
    else:
        extract.run()
    load.run()
    dbt_build()
    report.run()


if __name__ == "__main__":
    main()
