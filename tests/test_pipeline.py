"""End-to-end run over the sample payloads in tests/fixtures (no network)."""

import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("wh")
    db = tmp / "test.duckdb"
    env = {**os.environ, "DUCKDB_PATH": str(db), "REPORT_PATH": str(tmp / "report.html")}
    subprocess.run([sys.executable, "-m", "pipeline.run", "--fixtures"], cwd=ROOT, env=env,
                   check=True)
    with duckdb.connect(str(db), read_only=True) as con:
        yield con, tmp / "report.html"


def test_every_source_lands_in_raw(warehouse):
    warehouse, _ = warehouse
    counts = dict(warehouse.execute("select 'himalayas', count(*) from raw.himalayas union all "
                                "select 'remotive', count(*) from raw.remotive union all "
                                "select 'remoteok', count(*) from raw.remoteok").fetchall())
    assert counts == {"himalayas": 60, "remotive": 20, "remoteok": 25}


def test_salaries_are_annual_usd(warehouse):
    warehouse, _ = warehouse
    lo, hi = warehouse.execute("select min(salary_min_usd), max(salary_max_usd) "
                           "from intermediate.int_jobs").fetchone()
    assert lo >= 5_000 and hi <= 1_000_000


def test_remotive_free_text_salary_is_parsed(warehouse):
    warehouse, _ = warehouse
    n = warehouse.execute("select count(*) from intermediate.int_jobs "
                      "where source = 'remotive' and salary_min_usd is not null").fetchone()[0]
    assert n > 0


def test_python_is_detected_as_a_skill(warehouse):
    warehouse, _ = warehouse
    row = warehouse.execute("select n_jobs from marts.mart_skill_demand "
                        "where skill = 'Python'").fetchone()
    assert row and row[0] > 0


def test_go_is_case_sensitive(warehouse):
    warehouse, _ = warehouse
    # "go" as a verb appears in almost every posting; the language must not.
    share = warehouse.execute("select coalesce(max(share_of_jobs), 0) from marts.mart_skill_demand "
                          "where skill = 'Go'").fetchone()[0]
    assert share < 0.3


def test_report_is_rendered(warehouse):
    _, report = warehouse
    html = report.read_text(encoding="utf-8")
    assert "Most requested skills" in html
